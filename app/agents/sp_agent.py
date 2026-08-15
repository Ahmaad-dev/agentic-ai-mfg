"""
SP_Agent - Smart Planning Agent
"""
import json
import os
import logging
import subprocess
import sys as _sys
from pathlib import Path
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from .sp_tools_config import SP_TOOLS, SP_PIPELINES
from core.agent_config import HUMAN_IN_THE_LOOP

# StorageManager über runtime_storage (unterstützt LOCAL + AZURE)
_runtime_storage_dir = str(Path(__file__).parent.parent / "tools" / "smart-planning" / "runtime")
if _runtime_storage_dir not in _sys.path:
    _sys.path.insert(0, _runtime_storage_dir)
from runtime_storage import (get_storage as _get_storage,
                             get_iteration_folders_with_file as _get_iter_with_file,
                             get_latest_iteration_number as _get_latest_iter)

logger = logging.getLogger(__name__)

#: Exit-Code, mit dem ein Werkzeug sagt: "kein Fehler, aber es wartet eine menschliche
#: Entscheidung". Vergeben von generate_correction_llm.py, wenn zu diesem Snapshot bereits
#: ein Vorschlag offen ist.
WAITING_FOR_DECISION = 3


class SPAgent(BaseAgent):
    """Smart Planning Agent - Verwaltet Snapshots, Validierung und automatische Korrekturen"""
    
    def __init__(
        self,
        runtime_dir: Path,
        routing_description: str = None
    ):
        """
        Args:
            runtime_dir: Path zum runtime-Verzeichnis (wo die Python-Scripts liegen)
            routing_description: Routing-Beschreibung für Orchestrator (kommt aus agent_config.py)
        """
        # Minimaler System Prompt (wird nicht für LLM-Calls genutzt, nur für BaseAgent-Interface)
        system_prompt = "SP_Agent - Pure Executor für Smart Planning Tools und Pipelines."
        
        # Fallback routing_description falls nicht aus Config übergeben
        if not routing_description:
            routing_description = (
                "Smart Planning Agent - Snapshot-Verwaltung, Validierung und automatische Fehlerkorrektur.\n\n"
                "Zuständig für alle Smart Planning Anfragen:\n"
                "- Snapshots erstellen, validieren, korrigieren, umbenennen\n"
                "- Fehleranalyse und automatische Korrekturen\n"
                "- Audit-Reports generieren\n\n"
                "Trigger-Keywords: 'Snapshot', 'validieren', 'korrigieren', 'Fehler', 'Bericht'"
            )
        
        super().__init__(
            name="SP_Agent",
            system_prompt=system_prompt,
            description="Smart Planning Agent - Snapshot-Verwaltung und automatische Fehlerkorrektur",
            routing_description=routing_description,
            temperature=0.0  # Irrelevant, SP_Agent macht keine LLM-Calls
        )
        
        self.runtime_dir = Path(runtime_dir)
        
        if not self.runtime_dir.exists():
            raise ValueError(f"Runtime-Verzeichnis nicht gefunden: {runtime_dir}")
    
    def _run_tool(self, tool_name: str, args: List[str] = None) -> Dict:
        """Führt ein Python-Tool aus"""
        tool_info = SP_TOOLS.get(tool_name)
        if not tool_info:
            return {"success": False, "error": f"Unbekanntes Tool: {tool_name}"}
        
        script_path = self.runtime_dir / tool_info["script"]
        if not script_path.exists():
            return {"success": False, "error": f"Script nicht gefunden: {script_path}"}
        
        # sys.executable: Nutze das aktuell laufende Python (venv auf Windows, /usr/local/bin/python in Docker)
        cmd = [_sys.executable, str(script_path)]
        if args:
            # download_snapshot nimmt identifier (Name/UUID) als positionales Argument
            # rename_snapshot: args[0]=snapshot_id → --snapshot-id, args[1]=new_name → positional
            # identify_snapshot: args[0]=snapshot_id → --snapshot-id, weitere args bleiben positional
            # Alle anderen Tools: args[0] ist immer snapshot_id → --snapshot-id
            if tool_name == "download_snapshot":
                cmd.extend(args)  # positional identifier
            else:
                cmd.extend(["--snapshot-id", args[0]])
                if len(args) > 1:
                    cmd.extend(args[1:])  # z.B. new_name bei rename_snapshot
        
        logger.info(f"[{self.name}] Führe Tool aus: {tool_name} ({' '.join(cmd)})")
        
        try:
            # UTF-8 in BEIDE Richtungen erzwingen (15.08.2026).
            #
            # Ohne `PYTHONIOENCODING` erbt das Werkzeug die Konsolen-Codepage des Elternteils
            # — auf diesem System cp1252. Ein einzelnes Zeichen ausserhalb davon in einem
            # LLM-Text laesst dann das WERKZEUG abstuerzen, nicht etwa nur die Ausgabe
            # verstuemmeln: gemessen an einem "→" in `relevant_cards_reasoning`, das
            # `generate_correction_llm` beim blossen `print` mit UnicodeEncodeError beendete.
            # Der Korrekturvorschlag entstand deshalb nie, obwohl der Fehler korrekt erkannt
            # war. `errors="replace"` beim Lesen sorgt zusaetzlich dafuer, dass ein
            # unerwartetes Byte hoechstens ein Fragezeichen erzeugt und nie eine Ausnahme.
            umgebung = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
            result = subprocess.run(
                cmd,
                cwd=str(self.runtime_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=umgebung,
                timeout=90  # 90 Sekunden Timeout (bei VPN-Fehler soll schnell ein Fehler kommen)
            )
            
            base_result = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "tool": tool_name
            }

            # Exit-Code 3 heisst NICHT "kaputt", sondern "es wartet etwas auf eine
            # menschliche Entscheidung". Ohne diese Unterscheidung wiederholt die Pipeline
            # dreimal dasselbe und meldet am Ende einen Fehlschlag — obwohl alles richtig
            # gelaufen ist und der Nutzer nur handeln muss.
            if result.returncode == WAITING_FOR_DECISION:
                base_result["waiting_for_decision"] = True
            
            # Spezialfall: create_snapshot, download_snapshot → Parse Snapshot-Metadaten (Name, ID)
            if tool_name in ["create_snapshot", "download_snapshot"] and result.returncode == 0:
                snapshot_metadata = self._read_snapshot_metadata_from_stdout(result.stdout)
                if snapshot_metadata:
                    base_result["snapshot_metadata"] = snapshot_metadata
            
            # Spezialfall: validate_snapshot → Parse Validation-Daten UND Metadata
            if tool_name == "validate_snapshot" and result.returncode == 0 and args:
                snapshot_id = args[0] if args else None
                if snapshot_id:
                    # Lese Validation-Daten (Errors/Warnings)
                    validation_data = self._read_validation_data(snapshot_id)
                    if validation_data:
                        base_result["validation"] = validation_data
                    
                    # Lese AUCH Metadata (Name, ID, etc.)
                    snapshot_metadata = self._read_snapshot_metadata(snapshot_id)
                    if snapshot_metadata:
                        base_result["snapshot_metadata"] = snapshot_metadata
            
            # Spezialfall: rename_snapshot, identify_snapshot → Lese Metadata nach Erfolg
            if tool_name in ["rename_snapshot", "identify_snapshot"] and result.returncode == 0 and args:
                snapshot_id = args[0] if args else None
                if snapshot_id:
                    snapshot_metadata = self._read_snapshot_metadata(snapshot_id)
                    if snapshot_metadata:
                        base_result["snapshot_metadata"] = snapshot_metadata
            
            return base_result
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tool-Ausführung Timeout (>5min)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _read_snapshot_metadata_from_stdout(self, stdout: str) -> Optional[Dict]:
        """Extrahiert Snapshot-ID aus stdout und liest metadata.txt"""
        try:
            import re
            import json
            
            # Suche nach Snapshot-ID im stdout (UUID-Pattern)
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            matches = re.findall(uuid_pattern, stdout, re.IGNORECASE)
            
            if not matches:
                return None
            
            snapshot_id = matches[0]  # Erste gefundene UUID
            return self._read_snapshot_metadata(snapshot_id)
            
        except Exception as e:
            logger.warning(f"[{self.name}] Fehler beim Lesen der Snapshot-Metadaten aus stdout: {e}")
            return None
    
    def _read_snapshot_metadata(self, snapshot_id: str) -> Optional[Dict]:
        """Liest metadata.txt + LLM Corrections für eine gegebene Snapshot-ID"""
        try:
            import re
            
            storage = _get_storage()
            
            # Lese metadata.txt via StorageManager (LOCAL oder AZURE)
            content = storage.load_text(f"{snapshot_id}/metadata.txt")
            if content is None:
                return None
            
            # Extrahiere JSON-Block zwischen ```json und ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if not json_match:
                return None
            
            metadata = json.loads(json_match.group(1))
            
            # Lade LLM Corrections aus allen iteration-X Ordnern via StorageManager
            llm_corrections = []
            iteration_nums = sorted(_get_iter_with_file(snapshot_id, "llm_correction_proposal.json"))
            
            for iteration_num in iteration_nums:
                correction_data = storage.load_json(f"{snapshot_id}/iteration-{iteration_num}/llm_correction_proposal.json")
                if correction_data:
                    try:
                        proposal = correction_data.get("correction_proposal", {})
                        iter_n = correction_data.get("iteration", 0)
                        llm_corrections.append({
                            "iteration": iter_n,
                            "action": proposal.get("action"),
                            "target_path": proposal.get("target_path"),
                            "old_value": proposal.get("current_value"),
                            "new_value": proposal.get("new_value"),
                            "reasoning": proposal.get("reasoning")
                        })
                    except Exception as e:
                        logger.warning(f"[{self.name}] Fehler beim Lesen von iteration-{iteration_num}/llm_correction_proposal.json: {e}")
            
            # Füge Corrections zu Metadata hinzu
            if llm_corrections:
                metadata["llm_corrections"] = llm_corrections
            
            return metadata
            
        except Exception as e:
            logger.warning(f"[{self.name}] Fehler beim Lesen der Snapshot-Metadaten: {e}")
            return None
    
    def _read_validation_data(self, snapshot_id: str) -> Optional[Dict]:
        """Liest Validierungs-Daten für einen Snapshot (Fehler/Warnings)"""
        try:
            storage = _get_storage()
            
            # Lese snapshot-validation.json via StorageManager (LOCAL oder AZURE)
            validation_data = storage.load_json(f"{snapshot_id}/snapshot-validation.json")
            if validation_data is None:
                return None
            
            error_count = sum(1 for msg in validation_data if msg.get('level') == 'ERROR')
            warning_count = sum(1 for msg in validation_data if msg.get('level') == 'WARNING')
            
            errors = [msg for msg in validation_data if msg.get('level') == 'ERROR']
            warnings = [msg for msg in validation_data if msg.get('level') == 'WARNING']
            
            # Server-Validierungsstatus (optional - nur wenn uploaded)
            server_is_validated = False
            upload_data = storage.load_json(f"{snapshot_id}/upload-result.json")
            if upload_data:
                server_response = upload_data.get("server_response", {})
                server_is_validated = server_response.get("isSuccessfullyValidated", False)
            
            # WICHTIG: Snapshot ist VALIDE wenn KEINE ERRORS vorhanden sind (Warnings sind OK!)
            # Server-Status ist optional (nur relevant wenn Snapshot hochgeladen wurde)
            return {
                "is_valid": error_count == 0,  # Valide = Keine Errors (unabhängig von Upload)
                "server_validated": server_is_validated,  # Optionaler Server-Status
                "errors": error_count,
                "warnings": warning_count,
                "error_details": errors[:3],  # Max 3 Fehler
                "warning_details": warnings[:5]  # Max 5 Warnings
            }
            
        except Exception as e:
            logger.warning(f"[{self.name}] Fehler beim Lesen der Validation-Daten: {e}")
            return None
    
    def _execute_pipeline(self, pipeline_name: str, snapshot_id: Optional[str] = None) -> Dict:
        """Führt eine komplette Pipeline mit Retry-Logik aus"""
        pipeline = SP_PIPELINES.get(pipeline_name)

        # Die Sperre steckt in generate_correction_llm — dort ist sie richtig aufgehoben,
        # weil sie auch beim direkten Werkzeugaufruf greifen muss. Sie wuerde aber erst
        # NACH validate und identify zuschlagen, und identify kostet einen LLM-Aufruf.
        # Deshalb hier dieselbe Frage noch einmal, bevor der erste Schritt laeuft.
        if (pipeline and "generate_correction_llm" in (pipeline.get("steps") or [])
                and snapshot_id and HUMAN_IN_THE_LOOP):
            wartet = self._open_proposal_blocking(snapshot_id)
            if wartet:
                logger.info(f"[{self.name}] Pipeline '{pipeline_name}' haelt an: Vorschlag "
                            f"{wartet['proposal_id']} wartet auf eine Entscheidung")
                return {
                    "success": True,
                    "pipeline": pipeline_name,
                    "completed_steps": [],
                    "final_validation": None,
                    "analysis_scope": None,
                    "waiting_for_decision": True,
                    "open_proposal": wartet,
                }
        if not pipeline:
            return {"success": False, "error": f"Unbekannte Pipeline: {pipeline_name}"}
        
        logger.info(f"[{self.name}] Starte Pipeline: {pipeline['name']} für Snapshot: {snapshot_id}")
        
        # WICHTIG: Ohne Snapshot-ID können viele Tools nicht funktionieren!
        if not snapshot_id:
            logger.warning(f"[{self.name}] Pipeline gestartet OHNE Snapshot-ID - Tools könnten fehlschlagen")
        
        results = []
        max_retries = 2  # Jeder Schritt wird max 2x wiederholt
        
        for step in pipeline["steps"]:
            logger.info(f"[{self.name}] Pipeline-Schritt: {step}")
            
            # Versuche Schritt mit Retries
            attempt = 0
            tool_result = None
            
            while attempt <= max_retries:
                attempt += 1
                logger.info(f"[{self.name}] Versuch {attempt}/{max_retries + 1} für Schritt '{step}'")
                
                # Tool ausführen - MIT Snapshot-ID falls vorhanden
                args = [snapshot_id] if snapshot_id else []
                tool_result = self._run_tool(step, args)
                
                # Erfolg? → Weiter zum nächsten Schritt
                if tool_result["success"]:
                    logger.info(f"[{self.name}] Schritt '{step}' erfolgreich (Versuch {attempt})")
                    results.append({
                        "step": step,
                        "success": True,
                        "attempts": attempt,
                        "output": tool_result.get("stdout", ""),
                        "error": None
                    })
                    break
                
                # Wartet etwas auf eine Entscheidung, ist Wiederholen sinnlos: der Zustand
                # aendert sich nur durch einen Menschen, nicht durch einen zweiten Versuch.
                if tool_result.get("waiting_for_decision"):
                    logger.info(f"[{self.name}] Schritt '{step}' wartet auf eine menschliche "
                                f"Entscheidung - Pipeline haelt an (kein Fehlschlag)")
                    results.append({
                        "step": step,
                        "success": True,
                        "attempts": attempt,
                        "output": tool_result.get("stdout", ""),
                        "waiting_for_decision": True,
                        "error": None
                    })
                    return {
                        "success": True,
                        "pipeline": pipeline_name,
                        "completed_steps": results,
                        "final_validation": None,
                        "analysis_scope": None,
                        "waiting_for_decision": True,
                        "waiting_message": tool_result.get("stdout", ""),
                    }

                # Fehler → Prüfe ob Retry sinnvoll
                error_msg = tool_result.get("stderr", "") or tool_result.get("error", "")
                logger.warning(f"[{self.name}] Schritt '{step}' fehlgeschlagen (Versuch {attempt}): {error_msg[:200]}")
                
                # Bestimmte Fehler sind NICHT retry-fähig
                non_retryable_errors = [
                    "Snapshot nicht gefunden",
                    "Snapshot does not exist",
                    "Authentication failed",
                    "CLIENT_SECRET"
                ]
                
                if any(err in error_msg for err in non_retryable_errors):
                    logger.error(f"[{self.name}] Nicht-wiederholbarer Fehler erkannt")
                    break
                
                # Warte kurz vor Retry (falls temporäres Problem)
                if attempt <= max_retries:
                    import time
                    time.sleep(1)
            
            # Schritt auch nach Retries fehlgeschlagen?
            if not tool_result["success"]:
                logger.error(f"[{self.name}] Pipeline gestoppt bei Schritt '{step}' nach {attempt} Versuchen")
                
                # Bessere Fehleranalyse
                recovery_suggestion = self._suggest_recovery(step, tool_result)
                
                results.append({
                    "step": step,
                    "success": False,
                    "attempts": attempt,
                    "output": tool_result.get("stdout", ""),
                    "error": error_msg
                })
                
                return {
                    "success": False,
                    "pipeline": pipeline_name,
                    "completed_steps": results,
                    "failed_at": step,
                    "error": error_msg,
                    "recovery_suggestion": recovery_suggestion
                }
        
        logger.info(f"[{self.name}] Pipeline '{pipeline_name}' erfolgreich abgeschlossen")
        
        # Bei full_correction oder correction_from_validation: Prüfe finale Validierung
        final_validation_status = None
        if pipeline_name in ["full_correction", "correction_from_validation"] and snapshot_id:
            try:
                storage = _get_storage()
                
                # Lese upload-result.json via StorageManager (LOCAL oder AZURE)
                upload_data = storage.load_json(f"{snapshot_id}/upload-result.json")
                is_validated = False
                if upload_data:
                    server_response = upload_data.get("server_response", {})
                    is_validated = server_response.get("isSuccessfullyValidated", False)
                
                # Lese snapshot-validation.json für Fehler-Details
                error_count = 0
                warning_count = 0
                validation_data = storage.load_json(f"{snapshot_id}/snapshot-validation.json")
                if validation_data:
                    error_count = sum(1 for msg in validation_data if msg.get('level') == 'ERROR')
                    warning_count = sum(1 for msg in validation_data if msg.get('level') == 'WARNING')
                
                final_validation_status = {
                    "errors": error_count,
                    "warnings": warning_count,
                    "is_valid": error_count == 0,  # Valide = keine Errors (Upload-Status separat)
                    "server_validated": is_validated
                }
                
                logger.info(f"[{self.name}] Final Validation: is_valid={final_validation_status['is_valid']}, errors={error_count}, warnings={warning_count}")
                
            except Exception as e:
                logger.warning(f"[{self.name}] Could not read validation status: {e}")
        
        # Reichweite der reinen Analyse. Ohne diese Angaben weiss das Modell, das den
        # Text formuliert, NICHT, wie viel der Lauf abgedeckt hat — und hat im Lauf vom
        # 14.08.2026 prompt behauptet, alle Fehler seien behoben und der Snapshot valide,
        # obwohl ein Vorschlag fuer genau EINEN von drei Fehlern erzeugt und nichts
        # geschrieben wurde.
        analysis_scope = None
        if pipeline_name == "analyze_only" and snapshot_id:
            analysis_scope = self._describe_analysis_scope(snapshot_id)

        return {
            "success": True,
            "pipeline": pipeline_name,
            "completed_steps": results,
            "final_validation": final_validation_status,
            "analysis_scope": analysis_scope
        }
    
    def _open_proposal_blocking(self, snapshot_id: str) -> Optional[Dict]:
        """Wartet zu diesem Snapshot schon ein Vorschlag auf eine Entscheidung?

        Defensiv wie die Zwillingspruefung im Werkzeug: ist die Datenbank nicht erreichbar,
        wird NICHT gesperrt. Die eigentliche Sperre sitzt ohnehin im Anwenden-Pfad.
        """
        try:
            from db import repository as repo
            offen = [p for p in repo.list_open_proposals_as_dicts()
                     if p["snapshot_id"] == snapshot_id]
            return offen[0] if offen else None
        except Exception as exc:
            logger.warning(f"[{self.name}] Offene Vorschlaege nicht pruefbar: {exc}")
            return None

    def _describe_analysis_scope(self, snapshot_id: str) -> Optional[Dict]:
        """Was der Analyse-Lauf abgedeckt hat — und vor allem, was NICHT.

        `analyze_only` behandelt pro Durchlauf genau EINEN Fehler: `identify_error_llm`
        waehlt einen aus und priorisiert ihn, `generate_correction_llm` schlaegt dafuer
        einen Wert vor. Geschrieben wird nichts. Wer nur "Pipeline erfolgreich" sieht, haelt
        das fuer eine vollstaendige Korrektur — genau das ist passiert.

        Quelle sind die Artefakte des Laufs selbst, nicht eine erneute Pruefung: die
        `snapshot-validation.json` IM Iterationsordner ist der Stand, auf dem die Auswahl
        beruhte. Die Datei eine Ebene darueber wird von spaeteren Laeufen ueberschrieben und
        wuerde hier eine andere Zahl liefern als die, die der Lauf tatsaechlich gesehen hat.

        Defensiv: fehlt ein Artefakt, wird `None` geliefert und der Kontext bleibt wie
        bisher — lieber keine Angabe als eine falsche.
        """
        try:
            storage = _get_storage()
            n = _get_latest_iter(snapshot_id, require_file="llm_identify_response.json")
            if n is None:
                return None

            ident = storage.load_json(
                f"{snapshot_id}/iteration-{n}/llm_identify_response.json") or {}
            selected = ((ident.get("llm_analysis") or {}).get("selected_error") or {}).get("message")

            # Bevorzugt die Kopie IM Iterationsordner — sie ist der Stand, auf dem die
            # Auswahl beruhte. Die legt aber nur `apply_correction` beim Sichern an; ein
            # reiner Analyse-Lauf schreibt sie nie. Dann gilt die Datei eine Ebene darueber:
            # `validate_snapshot` hat sie als ERSTEN Schritt dieses Laufs geschrieben, sie
            # ist also genau der Stand, den der Lauf gesehen hat.
            #
            # Bis 15.08.2026 fehlte dieser Rueckfall, und das abschliessende `or []` machte
            # daraus ein klammheimliches "0 Fehler gefunden" — eine erfundene Zahl an genau
            # der Stelle, die Zahlen belastbar machen soll.
            messages = (storage.load_json(f"{snapshot_id}/iteration-{n}/snapshot-validation.json")
                        or storage.load_json(f"{snapshot_id}/snapshot-validation.json")
                        or [])
            errors = [m.get("message", "") for m in messages if m.get("level") == "ERROR"]
            warnings = [m.get("message", "") for m in messages if m.get("level") == "WARNING"]

            # Ein behandelter Fehler bei null gefundenen ist ein Widerspruch: dann ist die
            # Validierungsdatei nicht auffindbar oder veraltet. Lieber GAR KEINE Angabe als
            # eine falsche — der Vorbehalt entfaellt dann einfach.
            if selected and not errors:
                logger.warning(f"[{self.name}] Analyse-Reichweite nicht belastbar "
                               f"(behandelter Fehler, aber keine Validierungsmeldungen) - weggelassen")
                return None

            scope = {
                "errors_found": len(errors),
                "warnings_found": len(warnings),
                "handled_error": selected,
                "errors_not_addressed": [m for m in errors if m != selected],
                "snapshot_written": False,
                "uploaded_to_server": False,
                "awaiting_human_decision": True,
            }
            logger.info(
                f"[{self.name}] Analyse-Reichweite: {scope['errors_found']} Fehler gefunden, "
                f"1 behandelt, {len(scope['errors_not_addressed'])} unberuehrt, nichts geschrieben"
            )
            return scope
        except Exception as exc:
            logger.warning(f"[{self.name}] Analyse-Reichweite nicht ermittelbar: {exc}")
            return None

    def _suggest_recovery(self, failed_step: str, tool_result: Dict) -> Dict:
        """
        Analysiert Fehler und gibt STRUKTURIERTE Recovery-Daten zurück (keine fertigen Texte!)
        Der Orchestrator interpretiert diese dann natürlich für den User.
        """
        error_msg = tool_result.get("stderr", "") or tool_result.get("error", "")
        
        # Datei nicht gefunden → Vorheriger Schritt fehlt
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            if "last_search_results.json" in error_msg:
                # Bis 15.08.2026 stand hier "missing_step: identify_error_llm" — eine fest
                # verdrahtete VERMUTUNG. Sie war im gemessenen Fall falsch: innerhalb einer
                # Pipeline laeuft identify_error_llm IMMER vor generate_correction_llm, und
                # laut Log war es gelaufen. Es hatte nur nichts erzeugt, weil die
                # Snapshot-Daten fehlten. Der Nutzer bekam daraufhin den Rat, einen Schritt
                # nachzuholen, den das System selbst gerade ausgefuehrt hatte.
                # Jetzt wird die Tatsache genannt, nicht eine Ursache behauptet.
                return {
                    "error_type": "search_results_missing",
                    "required_file": "last_search_results.json",
                    "fact": ("Die Suche im Snapshot hat keine Ergebnisdatei erzeugt. "
                             "In einer Pipeline laeuft die Fehler-Identifikation davor, "
                             "sie hat also gelaufen, aber nichts geliefert."),
                    "likely_cause": ("Die Snapshot-Daten liegen lokal nicht vor - meist, "
                                     "weil der Snapshot nie heruntergeladen wurde."),
                    "suggestion": "check_snapshot_downloaded",
                }
            return {
                "error_type": "missing_file",
                "context": "prerequisite_step_failed"
            }
        
        # Snapshot nicht gefunden
        if "snapshot" in error_msg.lower() and ("not found" in error_msg.lower() or "exist" in error_msg.lower()):
            return {
                "error_type": "snapshot_not_found",
                "context": "invalid_or_nonexistent_snapshot_id"
            }
        
        # Auth-Fehler
        if "auth" in error_msg.lower() or "CLIENT_SECRET" in error_msg:
            return {
                "error_type": "authentication_failed",
                "config_issue": "CLIENT_SECRET"
            }
        
        # Validierungsfehler
        if "validation" in error_msg.lower() or "error" in failed_step.lower():
            return {
                "error_type": "validation_error",
                "context": "snapshot_has_uncorrectable_errors"
            }
        
        # Generischer Fehler
        return {
            "error_type": "unknown",
            "failed_step": failed_step
        }
    

    def execute_tool(self, tool_name: str, args: List[str] = None) -> Dict:
        """
        NEUE HAUPTMETHODE: Führt ein Tool aus und gibt strukturiertes Ergebnis zurück
        
        Args:
            tool_name: Name des Tools (z.B. "create_snapshot", "validate_snapshot")
            args: Liste von Argumenten (z.B. [snapshot_id, new_name])
        
        Returns:
            Dict mit:
            - success: bool
            - stdout: Tool-Output
            - stderr: Tool-Fehler
            - tool: Tool-Name
        """
        if args is None:
            args = []
        
        logger.info(f"[{self.name}] Führe Tool aus: {tool_name} mit Args: {args}")
        
        result = self._run_tool(tool_name, args)
        
        return result
    
    def execute_pipeline(self, pipeline_name: str, snapshot_id: Optional[str] = None) -> Dict:
        """
        NEUE HAUPTMETHODE: Führt eine Pipeline aus und gibt strukturiertes Ergebnis zurück.
        Bei Korrektur-Pipelines wird automatisch iteriert, bis keine Fehler mehr vorhanden
        sind oder die maximale Iterationszahl erreicht ist.
        
        Args:
            pipeline_name: Name der Pipeline (z.B. "full_correction")
            snapshot_id: Optional - Snapshot-ID
        
        Returns:
            Dict mit:
            - success: bool
            - pipeline: Pipeline-Name
            - completed_steps: List von Step-Ergebnissen
            - final_validation: Dict mit is_valid, errors, warnings (falls vorhanden)
            - total_iterations: Anzahl durchgeführter Iterationen
        """
        MAX_CORRECTION_ITERATIONS = 5
        is_correction_pipeline = pipeline_name in ["full_correction", "correction_from_validation"]

        iteration = 0
        last_result = None

        while True:
            iteration += 1
            logger.info(f"[{self.name}] Führe Pipeline aus: {pipeline_name} für Snapshot: {snapshot_id} (Iteration {iteration}/{MAX_CORRECTION_ITERATIONS})")

            last_result = self._execute_pipeline(pipeline_name, snapshot_id)

            # Kein Korrektur-Pipeline oder Pipeline-Schritt fehlgeschlagen → sofort zurückgeben
            if not is_correction_pipeline or not last_result.get("success"):
                break

            final_validation = last_result.get("final_validation")
            if not final_validation:
                break

            remaining_errors = final_validation.get("errors", 0)

            # Alle Fehler behoben → fertig
            if remaining_errors == 0:
                logger.info(f"[{self.name}] ✅ Snapshot valide nach {iteration} Iteration(en)")
                break

            # Maximale Iterationen erreicht
            if iteration >= MAX_CORRECTION_ITERATIONS:
                logger.warning(f"[{self.name}] ⚠ Maximale Iterationen ({MAX_CORRECTION_ITERATIONS}) erreicht – verbleibende Fehler: {remaining_errors}")
                break

            logger.info(f"[{self.name}] Noch {remaining_errors} Fehler nach Iteration {iteration}, starte neue Iteration...")

        last_result["total_iterations"] = iteration
        return last_result

