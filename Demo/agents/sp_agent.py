"""
SP_Agent - Smart Planning Agent
"""
import json
import logging
import subprocess
import sys as _sys
from pathlib import Path
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from .sp_tools_config import SP_TOOLS, SP_PIPELINES

# StorageManager über runtime_storage (unterstützt LOCAL + AZURE)
_runtime_storage_dir = str(Path(__file__).parent.parent / "smart-planning" / "runtime")
if _runtime_storage_dir not in _sys.path:
    _sys.path.insert(0, _runtime_storage_dir)
from runtime_storage import get_storage as _get_storage, get_iteration_folders_with_file as _get_iter_with_file

logger = logging.getLogger(__name__)


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
            result = subprocess.run(
                cmd,
                cwd=str(self.runtime_dir),
                capture_output=True,
                text=True,
                timeout=90  # 90 Sekunden Timeout (bei VPN-Fehler soll schnell ein Fehler kommen)
            )
            
            base_result = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "tool": tool_name
            }
            
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
        
        return {
            "success": True,
            "pipeline": pipeline_name,
            "completed_steps": results,
            "final_validation": final_validation_status
        }
    
    def _suggest_recovery(self, failed_step: str, tool_result: Dict) -> Dict:
        """
        Analysiert Fehler und gibt STRUKTURIERTE Recovery-Daten zurück (keine fertigen Texte!)
        Der Orchestrator interpretiert diese dann natürlich für den User.
        """
        error_msg = tool_result.get("stderr", "") or tool_result.get("error", "")
        
        # Datei nicht gefunden → Vorheriger Schritt fehlt
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            if "last_search_results.json" in error_msg:
                return {
                    "error_type": "missing_prerequisite",
                    "missing_step": "identify_error_llm",
                    "required_file": "last_search_results.json",
                    "suggestion": "run_identify_error_first"
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

