"""
SP_Agent - Smart Planning Agent
"""
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from .sp_tools_config import SP_TOOLS, SP_PIPELINES

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
        
        # Python-Executable aus venv verwenden
        python_exe = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
        
        cmd = [str(python_exe), str(script_path)]
        if args:
            cmd.extend(args)
        
        logger.info(f"[{self.name}] Führe Tool aus: {tool_name} ({' '.join(cmd)})")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.runtime_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 Minuten Timeout
            )
            
            base_result = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "tool": tool_name
            }
            
            # Spezialfall: create_snapshot → Parse Snapshot-Metadaten (Name, ID)
            if tool_name == "create_snapshot" and result.returncode == 0:
                snapshot_metadata = self._read_snapshot_metadata_from_stdout(result.stdout)
                if snapshot_metadata:
                    base_result["snapshot_metadata"] = snapshot_metadata
            
            # Spezialfall: validate_snapshot → Parse Validation-Daten
            if tool_name == "validate_snapshot" and result.returncode == 0 and args:
                snapshot_id = args[0] if args else None
                if snapshot_id:
                    validation_data = self._read_validation_data(snapshot_id)
                    if validation_data:
                        base_result["validation"] = validation_data
            
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
            snapshot_dir = self.runtime_dir.parent / "Snapshots" / snapshot_id
            metadata_file = snapshot_dir / "metadata.txt"
            
            if not metadata_file.exists():
                return None
            
            # Lese metadata.txt und extrahiere JSON
            with open(metadata_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extrahiere JSON-Block zwischen ```json und ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if not json_match:
                return None
            
            metadata = json.loads(json_match.group(1))
            
            # Gib ALLE Metadaten zurück (nicht nur 4 Felder)
            return metadata
            
        except Exception as e:
            logger.warning(f"[{self.name}] Fehler beim Lesen der Snapshot-Metadaten: {e}")
            return None
    
    def _read_validation_data(self, snapshot_id: str) -> Optional[Dict]:
        """Liest Validierungs-Daten für einen Snapshot (Fehler/Warnings)"""
        try:
            import json
            snapshot_dir = self.runtime_dir.parent / "Snapshots" / snapshot_id
            validation_file = snapshot_dir / "snapshot-validation.json"
            upload_result_file = snapshot_dir / "upload-result.json"
            
            if not validation_file.exists():
                return None
            
            with open(validation_file, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
            
            error_count = sum(1 for msg in validation_data if msg.get('level') == 'ERROR')
            warning_count = sum(1 for msg in validation_data if msg.get('level') == 'WARNING')
            
            errors = [msg for msg in validation_data if msg.get('level') == 'ERROR']
            warnings = [msg for msg in validation_data if msg.get('level') == 'WARNING']
            
            # Server-Validierungsstatus
            is_validated = False
            if upload_result_file.exists():
                with open(upload_result_file, 'r', encoding='utf-8') as f:
                    upload_data = json.load(f)
                    server_response = upload_data.get("server_response", {})
                    is_validated = server_response.get("isSuccessfullyValidated", False)
            
            return {
                "is_valid": is_validated and error_count == 0,
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
            # Lese upload-result.json um den Server-Validierungsstatus zu bekommen
            # WICHTIG: Nutze smart-planning/Snapshots, nicht relatives ../Snapshots
            snapshot_dir = self.runtime_dir.parent / "Snapshots" / snapshot_id
            upload_result_file = snapshot_dir / "upload-result.json"
            
            if upload_result_file.exists():
                try:
                    import json
                    with open(upload_result_file, 'r', encoding='utf-8') as f:
                        upload_data = json.load(f)
                    
                    server_response = upload_data.get("server_response", {})
                    is_validated = server_response.get("isSuccessfullyValidated", False)
                    
                    # Lese auch snapshot-validation.json für Fehler-Details
                    validation_file = snapshot_dir / "snapshot-validation.json"
                    error_count = 0
                    warning_count = 0
                    
                    if validation_file.exists():
                        with open(validation_file, 'r', encoding='utf-8') as f:
                            validation_data = json.load(f)
                        
                        error_count = sum(1 for msg in validation_data if msg.get('level') == 'ERROR')
                        warning_count = sum(1 for msg in validation_data if msg.get('level') == 'WARNING')
                    
                    final_validation_status = {
                        "errors": error_count,
                        "warnings": warning_count,
                        "is_valid": is_validated and error_count == 0
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
        NEUE HAUPTMETHODE: Führt eine Pipeline aus und gibt strukturiertes Ergebnis zurück
        
        Args:
            pipeline_name: Name der Pipeline (z.B. "full_correction")
            snapshot_id: Optional - Snapshot-ID
        
        Returns:
            Dict mit:
            - success: bool
            - pipeline: Pipeline-Name
            - completed_steps: List von Step-Ergebnissen
            - final_validation: Dict mit is_valid, errors, warnings (falls vorhanden)
        """
        logger.info(f"[{self.name}] Führe Pipeline aus: {pipeline_name} für Snapshot: {snapshot_id}")
        
        result = self._execute_pipeline(pipeline_name, snapshot_id)
        
        return result

