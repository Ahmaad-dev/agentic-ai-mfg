"""
OrchestrationAgent - Koordiniert alle Sub-Agenten
"""
import json
import logging
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from agent_config import CHAT_HISTORY_CONFIG

logger = logging.getLogger(__name__)


class OrchestrationAgent(BaseAgent):
    """Orchestration Agent - Koordiniert alle Sub-Agenten"""
    
    def __init__(
        self,
        aoai_client,
        model_name: str,
        agents: Dict[str, BaseAgent],
        router_temperature: float = 0,
        router_max_tokens: int = 200,
        interpretation_system_prompt: str = None
    ):
        """
        Args:
            aoai_client: Azure OpenAI Client
            model_name: Deployment-Name des Modells
            agents: Dictionary der verfügbaren Agenten {"chat": ChatAgent, "rag": RAGAgent}
            router_temperature: Temperature für Routing (default: 0 = deterministisch)
            router_max_tokens: Max Tokens für Router-Antwort
            interpretation_system_prompt: System Prompt für Sub-Agent-Interpretation (optional)
        """
        system_prompt = (
            "Du bist der Orchestration Agent eines Multi-Agent-Systems für eine Produktionsumgebung. "
            "Deine Aufgaben:\n"
            "1. Analysiere die User-Anfrage und entscheide, welcher Agent zuständig ist\n"
            "2. Leite die Anfrage an den passenden Agenten weiter\n"
            "3. Bei unklaren Anfragen: Chat Agent stellt Rückfragen\n"
            "4. Aggregiere und präsentiere die Ergebnisse\n\n"
            "Verfügbare Modi:\n"
            "- Chat Agent: Allgemeine Konversation, Erklärungen, Smalltalk\n"
            "- RAG Agent: Fragen zu internen Dokumenten, Richtlinien, technischen Spezifikationen\n"
            "- SP Agent: Smart Planning (Snapshots erstellen/validieren/korrigieren, Audit-Reports)\n\n"
            "Entscheide klug und transparent."
        )
        
        super().__init__(
            name="Orchestrator",
            system_prompt=system_prompt,
            temperature=router_temperature
        )
        
        self.aoai_client = aoai_client
        self.model_name = model_name
        self.agents = agents
        self.router_max_tokens = router_max_tokens
        self.interpretation_system_prompt = interpretation_system_prompt or (
            "Du bist ein hilfreicher Orchestration Agent. "
            "Interpretiere Sub-Agent-Ergebnisse und präsentiere sie benutzerfreundlich."
        )
        self.agentic_mode = True  # Aktiviert Multi-Step Planning
        self.last_snapshot_metadata = None  # Speichert letzte Snapshot-Metadaten für Chat Agent
    
    def _create_execution_plan(self, user_input: str, chat_history: List) -> Dict:
        """Erstellt einen Multi-Step Execution Plan für komplexe Anfragen"""
        
        # Kontext für bessere Planung
        # Nutze max_planning_pairs aus Config für konsistente History-Länge
        max_planning_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        context_summary = ""
        if chat_history:
            recent = chat_history[-(max_planning_pairs * 2):]  # 2 Paare = 4 Messages
            max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
            context_summary = "\n".join([
                f"{msg['role']}: {msg['content'][:max_chars]}"
                for msg in recent
            ])
        
        # Verfügbare Agenten und ihre Capabilities (DETAILLIERT)
        agent_capabilities = []
        for key, agent in self.agents.items():
            # Vollständige routing_description für detaillierte Planning-Infos
            agent_capabilities.append(
                f"**Agent: {key}**\n{agent.routing_description}"
            )
        
        planning_prompt = f"""Du bist ein Execution Planner für ein Multi-Agent System.

**KONVERSATIONSKONTEXT:**
{context_summary}

**USER ANFRAGE:**
{user_input}

**VERFÜGBARE AGENTEN UND IHRE TOOLS:**
{chr(10).join(agent_capabilities)}

**DEINE AUFGABE:**
Analysiere die User-Anfrage und erstelle einen SCHRITT-FÜR-SCHRITT Plan.

**BEI UNKLARHEIT:**
Wenn die Anfrage unklar ist oder Parameter fehlen:
- Route zu Chat Agent → LLM fragt natürlich nach
- Chat Agent kann im Kontext nachfragen: "Welchen Snapshot meinst du?"
- KEIN separater Clarify-Mode - halte es natürlich!

**WICHTIG: INFO-FRAGEN VS. ACTIONS**
1. **INFO-FRAGEN** (über bereits vorhandene Daten im Kontext):
   - "Was ist der Name vom Snapshot?" → Chat Agent (Info aus Historie/Metadata)
   - "Wer hat den Snapshot erstellt?" (dataModifiedBy) → Chat Agent (aus Metadata)
   - "Zeige mir die ID" → Chat Agent (Info aus Historie)
   - NUTZE CHAT AGENT wenn die Info bereits im Konversationskontext verfügbar ist!

2. **WARNING/ERROR DETAILS** (IMMER neue Daten abrufen!):
   - "Was sind die Warnings?" → SP Agent validate_snapshot (Details nie im Kontext!)
   - "was sind denn die 4?" → Wenn Kontext "4 Warnungen" zeigt → SP Agent validate_snapshot (Details!)
   - "Liste die Fehler auf" → SP Agent validate_snapshot (Messages nur dort!)
   - "Zeige Warning-Details" → SP Agent validate_snapshot (volle Info nur dort!)
   - WICHTIG: Auch wenn "4 Warnings" im Kontext steht, die Messages/Details sind NUR in validate_snapshot!
   - NIEMALS Chat Agent für Warning/Error Details - er hat nur Zahlen, nicht die Messages!

3. **ACTIONS** (neue Daten abrufen/verarbeiten):
   - "Validiere den Snapshot" → SP Agent (Tool ausführen)
   - "Erstelle Snapshot" → SP Agent (neuen Snapshot erstellen)
   - "Korrigiere Fehler" → SP Agent (Pipeline)

**WICHTIG: RE-PLANNING NACH FEHLER**
Falls die User-Anfrage einen "Recovery-Vorschlag" enthält (z.B. nach gescheitertem Versuch):
- Nutze den Vorschlag um einen BESSEREN Plan zu erstellen
- Führe fehlende Dependencies ZUERST aus
- Beispiel: "Recovery: Führe identify_error_llm zuerst aus" 
  → Plan: Step 1: identify_error_llm, Step 2: Original-Aktion wiederholen

**WICHTIG: BESTÄTIGUNGEN UND WIEDERHOLUNGEN**
Falls User sagt "ja", "mach das", "nochmal versuchen", "bitte beheben", etc.:
- PRÜFE KONTEXT: Was wurde zuletzt besprochen oder fehlgeschlagen?
- WENN vorherige Aktion fehlgeschlagen ist → WIEDERHOLE die Aktion (z.B. Pipeline nochmal ausführen)
- WENN User zugestimmt hat ("ja", "mach das") → FÜHRE die zuvor vorgeschlagene Aktion AUS
- WENN User nach Details fragt ("zeige details", "was sind die warnings", "gib mir die details"):
  * PRÜFE KONTEXT: Wurde gerade validiert oder gibt es Snapshot-Daten?
  * WENN Snapshot-ID im Kontext → Führe validate_snapshot aus (damit Warnings/Errors interpretiert werden)
  * NIEMALS audit_report wenn User nur Details SEHEN will - audit_report SPEICHERT nur Daten!
- Beispiele:
  * Kontext: "Pipeline schlug fehl", User: "nochmal versuchen" → Führe GLEICHE Pipeline nochmal aus
  * Kontext: "Soll ich korrigieren?", User: "ja" → Führe Korrektur-Pipeline aus
  * Kontext: "Snapshot hat Fehler", User: "bitte beheben" → Führe correction Pipeline aus
  * Kontext: "Snapshot hat 4 Warnungen", User: "zeige mir die details" → Führe validate_snapshot aus (nicht audit_report!)

**WICHTIGE PLANUNGS-REGELN:**

1. **Pipeline vs. Einzelschritte**:
   - SP_Agent hat vorkonfigurierte PIPELINES:
     * full_correction: validate → identify_error → generate_correction → apply → upload → re-validate
     * correction_from_validation: identify_error → generate_correction → apply → upload → re-validate (nutze wenn bereits validiert!)
     * analyze_only: nur Analyse, keine Änderungen
   - Wenn User sagt "korrigiere Snapshot" UND Snapshot wurde GERADE ERST ERSTELLT → full_correction Pipeline
   - Wenn User sagt "korrigiere/behebe Fehler" UND es gibt bereits Validierungsdaten im Kontext → correction_from_validation Pipeline
   - Wenn User will Schritte SEPARAT (z.B. "erst validieren, dann analysieren") → Multi-Step Plan

2. **Tool-Abhängigkeiten beachten**:
   - generate_correction_llm BENÖTIGT identify_error_llm (muss vorher laufen!)
   - apply_correction BENÖTIGT generate_correction_llm
   - NIEMALS einen Schritt überspringen der als Dependency markiert ist

3. **FEHLER-RECOVERY (WICHTIG!)**:
   - Wenn eine Pipeline fehlschlägt weil eine Dependency fehlt → Erstelle Multi-Step Plan mit fehlenden Schritten
   - Beispiel: "Korrigiere Snapshot" schlägt fehl bei generate_correction_llm (Datei fehlt)
     → Plan: Schritt 1: identify_error_llm ausführen, Schritt 2: correction_from_validation Pipeline nutzen
   - NUTZE DIE recovery_suggestion aus Fehlermeldungen um bessere Pläne zu erstellen!

4. **Single-Step vs. Multi-Step**:
   - Single-Step: Wenn die Anfrage mit EINEM Agent komplett lösbar ist
   - Multi-Step: Wenn mehrere Agenten koordiniert werden müssen ODER mehrere unabhängige Aktionen

5. **Agent Selection**:
   - chat: Allgemeine Fragen, Erklärungen, Analysen
   - rag: Suche in Dokumenten/Wissensbasis
   - sp: ALLES was mit Snapshots zu tun hat (erstellen, validieren, korrigieren, umbenennen)

**BEISPIELE:**

Anfrage: "Erstelle einen Snapshot"
→ {{"type": "single_step", "agent": "sp", "reasoning": "SP_Agent kann das direkt"}}

Anfrage: "was sind denn die 4?" (wenn Kontext "4 Warnungen" zeigt)
→ {{"type": "single_step", "agent": "sp", "action": "validate_snapshot für Details", "reasoning": "User will Warning-Details - Route zu SP Agent validate_snapshot"}}

Anfrage: "Korrigiere Snapshot X"
→ {{"type": "single_step", "agent": "sp", "action": "Nutze full_correction Pipeline für Snapshot X", "reasoning": "SP_Agent nutzt intern full_correction Pipeline"}}

Anfrage: "Behebe die Fehler" (wenn im Kontext bereits: "Snapshot wurde validiert, 4 Fehler gefunden")
→ {{"type": "single_step", "agent": "sp", "action": "Nutze correction_from_validation Pipeline", "reasoning": "Snapshot bereits validiert, starte direkt bei identify_error"}}

Anfrage: "Suche in Docs nach Snapshot-Regeln, dann validiere Snapshot abc-123"
→ {{
  "type": "multi_step",
  "steps": [
    {{"step": 1, "agent": "rag", "action": "Suche nach Snapshot-Validierungsregeln in Dokumenten", "reasoning": "RAG für Doku-Suche", "depends_on": []}},
    {{"step": 2, "agent": "sp", "action": "Validiere Snapshot abc-123", "reasoning": "SP_Agent validiert mit Kontext aus Schritt 1", "depends_on": [1]}}
  ],
  "reasoning": "RAG + SP müssen koordiniert werden"
}}

Anfrage: "Validiere den Snapshot und wenn Fehler, korrigiere sie"
→ {{
  "type": "multi_step",
  "steps": [
    {{"step": 1, "agent": "sp", "action": "Validiere Snapshot", "reasoning": "Erst prüfen ob Fehler vorhanden", "depends_on": []}},
    {{"step": 2, "agent": "sp", "action": "Nutze correction_from_validation Pipeline falls Fehler gefunden", "reasoning": "Conditional Korrektur - Snapshot bereits validiert in Schritt 1", "depends_on": [1]}}
  ],
  "reasoning": "Conditional Workflow - erst prüfen, dann handeln"
}}

Antworte NUR mit JSON im folgenden Format:
{{
  "type": "single_step" | "multi_step",
  "agent": "agent_key (nur bei single_step)",
  "steps": [
    {{"step": number, "agent": "key", "action": "description", "reasoning": "why", "depends_on": [step_numbers]}}
  ],
  "reasoning": "Begründung für die Planung"
}}"""
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Execution Planner. Antworte nur mit JSON."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.3,  # Deterministischer für Planung
                max_tokens=800
            )
            
            output = response.choices[0].message.content.strip()
            
            # JSON bereinigen
            if output.startswith("```json"):
                output = output[7:]
            if output.startswith("```"):
                output = output[3:]
            if output.endswith("```"):
                output = output[:-3]
            
            plan = json.loads(output.strip())
            
            logger.info(f"[{self.name}] Execution Plan erstellt: {plan['type']}")
            if plan['type'] == 'multi_step':
                logger.info(f"[{self.name}] Plan mit {len(plan.get('steps', []))} Schritten")
            
            return plan
            
        except Exception as e:
            logger.error(f"[{self.name}] Planning fehlgeschlagen: {e}")
            # Fallback: Single-Step mit Chat
            return {
                "type": "single_step",
                "agent": "chat",
                "reasoning": f"Planning-Fehler, Fallback zu Chat: {str(e)}"
            }
    
    def _execute_plan(self, plan: Dict, user_input: str, chat_history: List) -> Dict:
        """Führt einen Multi-Step Execution Plan aus"""
        
        plan_type = plan.get("type")
        
        # Single-Step: Direkt an Agent weiterleiten
        if plan_type == "single_step":
            agent_key = plan.get("agent")
            if agent_key not in self.agents:
                return {
                    "response": f"Fehler: Agent '{agent_key}' nicht gefunden",
                    "metadata": {"error": "unknown_agent"}
                }
            
            # SP_Agent → NEUE direkte Execution
            if agent_key == "sp":
                logger.info(f"[{self.name}] Single-Step Execution mit SP_Agent (NEUE Methode)")
                return self._execute_sp_agent(user_input, chat_history, {"chat_history": chat_history})
            
            # Chat/RAG → Alte Methode (behält execute())
            agent = self.agents[agent_key]
            
            # Erweitere Kontext mit letzten Snapshot-Metadaten (für Chat Agent)
            enhanced_context = {"chat_history": chat_history}
            if agent_key == "chat" and self.last_snapshot_metadata:
                enhanced_context["last_snapshot_metadata"] = self.last_snapshot_metadata
                logger.info(f"[{self.name}] Snapshot-Metadaten an Chat Agent weitergegeben")
            
            result = agent.execute(user_input, enhanced_context)
            
            # WICHTIG: Extrahiere recovery_suggestion BEVOR Interpretation (sonst geht sie verloren!)
            recovery_hint = None
            raw_response = result.get("response", {})
            if isinstance(raw_response, dict):
                recovery_hint = raw_response.get("recovery_suggestion")
                if recovery_hint:
                    logger.info(f"[{self.name}] Recovery-Suggestion gefunden: {recovery_hint[:100]}")
                    # Speichere in metadata für Re-Planning Loop
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["recovery_suggestion"] = recovery_hint
            
            # Interpretation
            interpreted_response = self._interpret_subagent_result(
                user_input=user_input,
                agent_name=agent_key,
                agent_result=result,
                chat_history=chat_history
            )
            result["response"] = interpreted_response
            result["metadata"]["execution_plan"] = plan
            
            return result
        
        # Multi-Step: Schrittweise Ausführung
        if plan_type == "multi_step":
            steps = plan.get("steps", [])
            step_results = []
            accumulated_context = {"chat_history": chat_history, "step_outputs": {}}
            
            logger.info(f"[{self.name}] Starte Multi-Step Execution mit {len(steps)} Schritten")
            
            for step in steps:
                step_num = step.get("step")
                agent_key = step.get("agent")
                action = step.get("action")
                depends_on = step.get("depends_on", [])
                
                logger.info(f"[{self.name}] Schritt {step_num}/{len(steps)}: {action} (Agent: {agent_key})")
                
                # Prüfe ob Agent existiert
                if agent_key not in self.agents:
                    error_msg = f"Fehler in Schritt {step_num}: Agent '{agent_key}' nicht gefunden"
                    logger.error(f"[{self.name}] {error_msg}")
                    return {
                        "response": error_msg,
                        "metadata": {
                            "error": "plan_execution_failed",
                            "failed_step": step_num,
                            "completed_steps": step_results
                        }
                    }
                
                # Dependency Context erstellen
                dependency_context = ""
                if depends_on:
                    for dep_step in depends_on:
                        if dep_step in accumulated_context["step_outputs"]:
                            prev_result = accumulated_context["step_outputs"][dep_step]
                            dependency_context += f"\n\nErgebnis von Schritt {dep_step}:\n{prev_result[:500]}"
                
                # Agent-spezifischer Input erstellen
                agent_input = action
                if dependency_context:
                    agent_input = f"{action}\n\nKONTEXT AUS VORHERIGEN SCHRITTEN:{dependency_context}"
                
                # SP_Agent → NEUE direkte Execution
                if agent_key == "sp":
                    logger.info(f"[{self.name}] Multi-Step Schritt {step_num}: SP_Agent (NEUE Methode)")
                    result = self._execute_sp_agent(agent_input, chat_history, accumulated_context)
                else:
                    # Chat/RAG → Alte Methode
                    agent = self.agents[agent_key]
                    result = agent.execute(agent_input, accumulated_context)
                
                # Ergebnis speichern
                response_text = result.get("response", "")
                if isinstance(response_text, dict):
                    # Bei rohen Tool-Outputs (SP_Agent)
                    response_text = response_text.get("stdout", str(response_text))[:1000]
                
                step_results.append({
                    "step": step_num,
                    "agent": agent_key,
                    "action": action,
                    "success": result.get("metadata", {}).get("success", True),
                    "response": response_text
                })
                
                # Context für nächste Schritte aktualisieren
                accumulated_context["step_outputs"][step_num] = response_text
                
                # Bei Fehler: Prüfe recovery_suggestion
                if not result.get("metadata", {}).get("success", True):
                    logger.warning(f"[{self.name}] Schritt {step_num} fehlgeschlagen")
                    
                    # Hole recovery_suggestion aus der Response
                    recovery_hint = None
                    if isinstance(result.get("response"), dict):
                        recovery_hint = result["response"].get("recovery_suggestion")
                    
                    if recovery_hint:
                        logger.info(f"[{self.name}] Recovery-Vorschlag verfügbar: {recovery_hint[:200]}")
                        # Speichere für finale Interpretation
                        step_results[-1]["recovery_suggestion"] = recovery_hint
                    
                    # Breche ab (User kann dann basierend auf recovery_suggestion neu planen)
                    break
            
            # Finale Interpretation aller Schritte
            summary = self._summarize_multi_step_execution(
                user_input=user_input,
                plan=plan,
                step_results=step_results,
                chat_history=chat_history
            )
            
            # Prüfe ob ein Schritt eine recovery_suggestion hat
            final_recovery = None
            for step_result in step_results:
                if "recovery_suggestion" in step_result:
                    final_recovery = step_result["recovery_suggestion"]
                    break
            
            metadata = {
                "execution_plan": plan,
                "completed_steps": step_results,
                "total_steps": len(steps),
                "agentic_execution": True
            }
            
            # Füge recovery_suggestion hinzu falls vorhanden
            if final_recovery:
                metadata["recovery_suggestion"] = final_recovery
                logger.info(f"[{self.name}] Multi-Step Recovery-Suggestion weitergeleitet: {final_recovery[:100]}")
            
            return {
                "response": summary,
                "metadata": metadata
            }
        
        # Unbekannter Plan-Typ
        return {
            "response": f"Fehler: Unbekannter Plan-Typ '{plan_type}'",
            "metadata": {"error": "invalid_plan_type"}
        }
    
    def _summarize_multi_step_execution(
        self,
        user_input: str,
        plan: Dict,
        step_results: List[Dict],
        chat_history: List
    ) -> str:
        """Fasst die Multi-Step Execution zusammen"""
        
        # Kontext - nutze zentrale Config
        max_summary_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        context_summary = ""
        if chat_history:
            recent = chat_history[-(max_summary_pairs * 2):]
            context_summary = "\n".join([
                f"{msg['role']}: {msg['content'][:100]}"
                for msg in recent
            ])
        
        # Schritte zusammenfassen
        steps_summary = ""
        for step in step_results:
            status = "✅" if step.get("success", True) else "❌"
            steps_summary += f"\n{status} Schritt {step['step']}: {step['action'][:100]}\n   Ergebnis: {step['response'][:200]}...\n"
        
        prompt = f"""Fasse die Ergebnisse einer Multi-Step Execution zusammen.

**KONTEXT:**
{context_summary}

**URSPRÜNGLICHE ANFRAGE:**
{user_input}

**DURCHGEFÜHRTE SCHRITTE:**
{steps_summary}

**DEINE AUFGABE:**
Erstelle eine prägnante, benutzerfreundliche Zusammenfassung:
1. Was wurde erreicht?
2. Wichtigste Ergebnisse
3. Nächste Schritte (falls relevant)

Sei natürlich und passe Tonfall an User-Frage an. 2-5 Sätze je nach Komplexität.
"""
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.interpretation_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"[{self.name}] Summarization fehlgeschlagen: {e}")
            # KEIN hardcodierter Fallback - gebe technische Info zurück
            return f"[SUMMARIZATION ERROR] {str(e)}"
    
    def _interpret_subagent_result(
        self, 
        user_input: str, 
        agent_name: str, 
        agent_result: Dict,
        chat_history: List
    ) -> str:
        """Interpretiert Sub-Agent-Ergebnisse und generiert kontextbezogene Antwort"""
        
        metadata = agent_result.get("metadata", {})
        raw_response = agent_result.get("response", {})
        
        # Kontext für bessere Interpretation - nutze zentrale Config
        max_interpret_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        context_summary = ""
        if chat_history:
            recent = chat_history[-(max_interpret_pairs * 2):]
            max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
            context_summary = "\n".join([
                f"{msg['role']}: {msg['content'][:max_chars]}"
                for msg in recent
            ])
        
        # === SP_Agent: Tool/Pipeline-Ergebnisse ===
        if metadata.get("intent") == "tool":
            tool_name = metadata.get("tool")
            tool_desc = metadata.get("tool_description")
            success = metadata.get("success")
            stdout = raw_response.get("stdout", "")
            stderr = raw_response.get("stderr", "")
            
            summary = f"""**Ausgeführtes Tool:** {tool_name}
**Beschreibung:** {tool_desc}
**Status:** {"Erfolgreich" if success else "Fehlgeschlagen"}
**Output:** {stdout[:1500]}
**Fehler:** {stderr[:500] if stderr else "Keine"}"""
            
        elif metadata.get("intent") == "pipeline":
            pipeline_name = metadata.get("pipeline")
            pipeline_desc = metadata.get("pipeline_description")
            success = metadata.get("success")
            
            if success:
                steps = raw_response.get("completed_steps", [])
                step_summary = "\n".join([
                    f"- {s['step']}: {'✅' if s['success'] else '❌'} (Versuche: {s.get('attempts', 1)}) {s.get('output', '')[:200]}"
                    for s in steps
                ])
                summary = f"""**Pipeline:** {pipeline_name}
**Beschreibung:** {pipeline_desc}
**Status:** Erfolgreich abgeschlossen
**Durchgeführte Schritte:**
{step_summary}"""
            else:
                failed_step = raw_response.get("failed_at", "unbekannt")
                error = raw_response.get("error", "Unbekannter Fehler")
                recovery_suggestion = raw_response.get("recovery_suggestion", "")
                attempts = max([s.get('attempts', 1) for s in raw_response.get("completed_steps", [])], default=1)
                
                summary = f"""**Pipeline:** {pipeline_name}
**Beschreibung:** {pipeline_desc}
**Status:** Fehlgeschlagen bei Schritt '{failed_step}' (nach {attempts} Versuchen)
**Fehler:** {error}
**Vorschlag:** {recovery_suggestion}"""
        
        # === ChatAgent: Allgemeine Konversation ===
        elif agent_name == "chat":
            confidence = metadata.get("confidence", "unknown")
            summary = f"""**Agent:** Chat Agent (Allgemeine Konversation)
**Antwort des Agents:**
{raw_response if isinstance(raw_response, str) else str(raw_response)[:1500]}
**Confidence:** {confidence}"""
        
        # === RAGAgent: Wissensbasis-gestützt ===
        elif agent_name == "rag":
            sources = metadata.get("sources", [])
            relevance = metadata.get("relevance_score", 0.0)
            retrieval_success = metadata.get("retrieval_success", False)
            
            sources_str = "\n".join([f"  - {s}" for s in sources]) if sources else "  Keine"
            summary = f"""**Agent:** RAG Agent (Wissensbasis)
**Retrieval Status:** {"Erfolgreich" if retrieval_success else "Keine relevanten Dokumente"}
**Relevanz-Score:** {relevance:.3f}
**Quellen:**
{sources_str}
**Antwort des Agents:**
{raw_response if isinstance(raw_response, str) else str(raw_response)[:1500]}"""
        
        else:
            # Fallback für unbekannte Agent-Typen
            summary = f"""**Agent:** {agent_name}
**Ergebnis:**
{str(raw_response)[:1000]}"""
        
        # LLM interpretiert und generiert natürliche Antwort
        prompt = f"""Ein Sub-Agent hat eine Aufgabe ausgeführt und du sollst das Ergebnis für den User interpretieren.

**KONVERSATIONSKONTEXT:**
{context_summary}

**USER FRAGE:**
{user_input}

**SUB-AGENT:** {agent_name} Agent

**ERGEBNIS (roh):**
{summary}

**DEINE AUFGABE:**
Beantworte die User-Frage basierend auf dem Sub-Agent-Ergebnis in natürlicher, präziser Sprache.

**REGELN:**
- Antworte DIREKT an den Benutzer (als wärst DU der Experte, nicht "Der Agent sagt...")
- Bei Validierungsdaten: Extrahiere relevante Fehler/Warnungen und erkläre sie
- Bei Fehlern mit Recovery-Vorschlag: Erkläre kurz was schiefging und biete Hilfe an
- Sei natürlich, freundlich und passe Tonfall/Detailgrad an die User-Frage an
- 2-5 Sätze je nach Komplexität

ANTWORTE NUR MIT DER INTERPRETIERTEN NACHRICHT (keine JSON, keine Anführungszeichen)"""
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.interpretation_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            interpretation = response.choices[0].message.content.strip()
            logger.info(f"[{self.name}] Interpretierte Antwort: {interpretation[:100]}...")
            
            return interpretation
            
        except Exception as e:
            logger.error(f"[{self.name}] Interpretation fehlgeschlagen: {e}")
            # KEIN hardcodierter Fallback - gebe technische Info zurück
            return f"[INTERPRETATION ERROR] {str(e)}"
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Orchestriert die Anfrage - mit agentic Planning und Adaptive Re-Planning"""
        logger.info(f"[{self.name}] Orchestriere Anfrage: {user_input[:100]}")
        
        chat_history = context.get("chat_history", []) if context else []
        
        # AGENTIC MODE: Erstelle Execution Plan mit Adaptive Re-Planning
        if self.agentic_mode:
            max_replanning_attempts = 2  # Max 2 Re-Planning Versuche
            attempt = 0
            original_input = user_input
            
            while attempt <= max_replanning_attempts:
                attempt += 1
                logger.info(f"[{self.name}] Agentic Mode: Planning-Versuch {attempt}/{max_replanning_attempts + 1}")
                
                # Erstelle Execution Plan
                plan = self._create_execution_plan(user_input, chat_history)
                
                # Plan ausführen
                result = self._execute_plan(plan, user_input, chat_history)
                
                # Metadata erweitern
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["agentic_mode"] = True
                result["metadata"]["plan_type"] = plan.get("type")
                result["metadata"]["planning_attempts"] = attempt
                
                # ERFOLG? → Prüfe explizit (KEIN Default=True, das wäre falsch!)
                success = result.get("metadata", {}).get("success")
                if success is None:
                    # Wenn success nicht gesetzt ist, betrachte als Erfolg (z.B. bei Info-Antworten)
                    success = True
                
                if success:
                    logger.info(f"[{self.name}] ✅ Execution erfolgreich nach {attempt} Versuch(en)")
                    return result
                
                # FEHLER → Prüfe ob Re-Planning möglich
                logger.warning(f"[{self.name}] ⚠️ Execution fehlgeschlagen (Versuch {attempt})")
                
                # Hole recovery_suggestion aus METADATA (nicht response, da response jetzt interpretiert ist!)
                recovery_hint = result.get("metadata", {}).get("recovery_suggestion")
                
                # Kein Re-Planning mehr möglich?
                if attempt > max_replanning_attempts:
                    logger.error(f"[{self.name}] Max Re-Planning Versuche erreicht")
                    break
                
                # Keine recovery_suggestion vorhanden?
                if not recovery_hint:
                    logger.warning(f"[{self.name}] Keine recovery_suggestion vorhanden, kann nicht re-planen")
                    logger.debug(f"[{self.name}] Result metadata: {result.get('metadata', {})}")
                    break
                
                # RE-PLANNING: Erstelle neuen Plan basierend auf recovery_suggestion
                logger.info(f"[{self.name}] 🔄 RE-PLANNING basierend auf: {recovery_hint[:100]}")
                
                # Modifiziere User-Input für Re-Planning
                user_input = (
                    f"{original_input}\n\n"
                    f"WICHTIG: Der vorherige Versuch schlug fehl. Recovery-Vorschlag: {recovery_hint}\n"
                    f"Erstelle einen neuen Plan der dieses Problem behebt."
                )
                
                # Füge Fehler-Context zur Chat-History hinzu
                chat_history.append({
                    "role": "assistant", 
                    "content": f"Fehler bei Versuch {attempt}: {recovery_hint[:200]}"
                })
            
            # Nach allen Versuchen: Gib letztes Ergebnis zurück
            result["metadata"]["replanning_exhausted"] = True
            return result
        
        return result
    
    def _execute_sp_agent(self, user_input: str, chat_history: List, context: Dict) -> Dict:
        """
        NEUE METHODE: Führt SP_Agent mit direkter Tool/Pipeline Auswahl aus
        - Analysiert User-Intent für Smart Planning
        - Ruft execute_tool() oder execute_pipeline() direkt auf
        - Interpretiert Ergebnisse im Orchestrator
        """
        sp_agent = self.agents.get("sp")
        if not sp_agent:
            return {
                "response": "SP_Agent nicht verfügbar",
                "metadata": {"error": "sp_agent_missing"}
            }
        
        # Extrahiere Snapshot-ID aus Historie (UUID-Pattern)
        snapshot_id_from_history = self._extract_snapshot_id_from_history(chat_history)
        
        # Analysiere was User will
        intent_prompt = f"""Analysiere die User-Anfrage für Smart Planning Operationen.

**KONVERSATIONSKONTEXT:**
{self._get_context_summary(chat_history)}

**AKTUELLE ANFRAGE:**
{user_input}

**SNAPSHOT-ID AUS HISTORIE:** {snapshot_id_from_history or "Keine gefunden"}

**VERFÜGBARE ACTIONS:**
- create_snapshot: Erstellt neuen Snapshot
- validate_snapshot: Validiert existierenden Snapshot UND zeigt Details (Errors/Warnings)
- rename_snapshot: Ändert Snapshot-Namen
- full_correction (Pipeline): validate → identify → correct → upload → re-validate
- correction_from_validation (Pipeline): identify → correct → upload → re-validate (nutze wenn bereits validiert!)
- identify_error_llm: Analysiert Validierungsfehler
- generate_audit_report: Erstellt formalen Prüfbericht/Dokumentation (NICHT zum Anzeigen von Details!)

**WICHTIGE REGELN:**
1. validate_snapshot vs. generate_audit_report:
   - User will Details SEHEN ("zeige details", "was sind die warnings", "gib mir die fehler") → validate_snapshot
   - User will formalen BERICHT ("erstelle bericht", "audit report", "dokumentation", "prüfbericht") → generate_audit_report
   - NIEMALS audit_report nur um Details anzuzeigen!

2. Pipeline-Auswahl:
   - "Korrigiere Snapshot" + NEU ERSTELLT → full_correction
   - "Korrigiere Snapshot" + BEREITS VALIDIERT → correction_from_validation
   - Prüfe Kontext auf Hinweise wie "wurde validiert", "Fehler gefunden"

3. Snapshot-ID Extraktion:
   - Wenn User "den Snapshot" sagt → nutze ID aus Historie
   - Bei UUID-Erwähnung → diese verwenden
   - Falls keine ID: null (außer bei create_snapshot)

4. Parameter für rename_snapshot:
   - new_name: String aus User-Input extrahieren

Antworte NUR mit JSON:
{{
  "action_type": "tool" | "pipeline",
  "action_name": "create_snapshot" | "validate_snapshot" | "full_correction" | etc.,
  "snapshot_id": "UUID oder null",
  "parameters": {{"new_name": "..." (nur bei rename_snapshot)}},
  "reasoning": "Kurze Begründung"
}}
"""
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Du bist ein SP_Agent Intent Analyzer. Antworte nur mit JSON."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            output = response.choices[0].message.content.strip()
            if output.startswith("```json"):
                output = output[7:]
            if output.startswith("```"):
                output = output[3:]
            if output.endswith("```"):
                output = output[:-3]
            
            intent = json.loads(output.strip())
            logger.info(f"[{self.name}] SP_Agent Intent: {intent['action_type']} - {intent['action_name']}")
            
            # Führe Action aus
            if intent["action_type"] == "pipeline":
                result = sp_agent.execute_pipeline(
                    pipeline_name=intent["action_name"],
                    snapshot_id=intent.get("snapshot_id")
                )
                
                # Interpretiere Pipeline-Ergebnis
                interpreted = self._interpret_sp_result(
                    action_type="pipeline",
                    action_name=intent["action_name"],
                    result=result,
                    user_input=user_input,
                    chat_history=chat_history
                )
                
                return {
                    "response": interpreted,
                    "metadata": {
                        "agent": "sp",
                        "action_type": "pipeline",
                        "pipeline": intent["action_name"],
                        "success": result["success"],
                        "final_validation": result.get("final_validation")
                    }
                }
            
            elif intent["action_type"] == "tool":
                # Baue Argument-Liste
                args = []
                snapshot_id = intent.get("snapshot_id")
                
                if intent["action_name"] == "rename_snapshot":
                    new_name = intent.get("parameters", {}).get("new_name")
                    if snapshot_id and new_name:
                        args = [snapshot_id, new_name]
                elif snapshot_id:
                    args = [snapshot_id]
                
                result = sp_agent.execute_tool(
                    tool_name=intent["action_name"],
                    args=args
                )
                
                # Speichere Snapshot-Metadaten für späteren Zugriff
                if intent["action_name"] == "create_snapshot" and "snapshot_metadata" in result:
                    self.last_snapshot_metadata = result["snapshot_metadata"]
                    logger.info(f"[{self.name}] Snapshot-Metadaten gespeichert für späteren Zugriff")
                
                # Interpretiere Tool-Ergebnis
                interpreted = self._interpret_sp_result(
                    action_type="tool",
                    action_name=intent["action_name"],
                    result=result,
                    user_input=user_input,
                    chat_history=chat_history
                )
                
                return {
                    "response": interpreted,
                    "metadata": {
                        "agent": "sp",
                        "action_type": "tool",
                        "tool": intent["action_name"],
                        "success": result["success"]
                    }
                }
            
        except Exception as e:
            logger.error(f"[{self.name}] SP_Agent Execution fehlgeschlagen: {e}")
            return {
                "response": f"Fehler bei Smart Planning Operation: {str(e)}",
                "metadata": {"agent": "sp", "error": str(e)}
            }
    
    def _extract_snapshot_id_from_history(self, chat_history: List) -> Optional[str]:
        """Extrahiert die letzte erwähnte Snapshot-ID (UUID) aus der Chat-Historie"""
        import re
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        
        for msg in reversed(chat_history):
            content = msg.get("content", "")
            matches = re.findall(uuid_pattern, content, re.IGNORECASE)
            if matches:
                return matches[-1]  # Neueste ID in dieser Message
        
        return None
    
    def _get_context_summary(self, chat_history: List, max_messages: int = 3) -> str:
        """Erstellt eine kompakte Zusammenfassung der letzten Messages"""
        if not chat_history:
            return "Keine Historie"
        
        recent = chat_history[-max_messages:]
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:200]
            lines.append(f"{role}: {content}...")
        
        return "\n".join(lines)
    
    def _interpret_sp_result(self, action_type: str, action_name: str, result: Dict, user_input: str, chat_history: List) -> str:
        """Interpretiert SP_Agent Ergebnisse mit LLM (keine hartcodierten Antworten!)"""
        
        # Extrahiere relevante Daten aus Result
        success = result.get("success", False)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        error = result.get("error", "")
        
        # Kontext zusammenstellen
        context_parts = []
        
        if action_type == "pipeline":
            context_parts.append(f"Pipeline '{action_name}' wurde ausgeführt.")
            context_parts.append(f"Status: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
            
            if not success:
                failed_at = result.get("failed_at", "unbekannt")
                context_parts.append(f"Fehlgeschlagen bei Schritt: {failed_at}")
                context_parts.append(f"Fehler: {error or stderr}")
                
                # Recovery-Suggestion ist jetzt strukturiert (Dict statt String)
                recovery = result.get("recovery_suggestion")
                if recovery:
                    if isinstance(recovery, dict):
                        # Strukturierte Recovery-Daten
                        error_type = recovery.get("error_type", "unknown")
                        context_parts.append(f"Fehlertyp: {error_type}")
                        
                        if error_type == "missing_prerequisite":
                            context_parts.append(f"Fehlender Schritt: {recovery.get('missing_step')}")
                            context_parts.append(f"Benötigte Datei: {recovery.get('required_file')}")
                        elif error_type == "snapshot_not_found":
                            context_parts.append("Snapshot-ID ungültig oder nicht existent")
                        elif error_type == "authentication_failed":
                            context_parts.append(f"Konfigurationsproblem: {recovery.get('config_issue')}")
                        
                        # Füge alle recovery-Felder hinzu für LLM-Kontext
                        for key, value in recovery.items():
                            if key not in ["error_type"]:
                                context_parts.append(f"{key}: {value}")
                    else:
                        # Fallback für alte String-Recovery (während Übergangszeit)
                        context_parts.append(f"Recovery-Info: {recovery}")
            else:
                completed = result.get("completed_steps", [])
                # completed_steps ist eine Liste von Dicts, extrahiere step-Namen
                step_names = [s.get("step", "unknown") for s in completed]
                context_parts.append(f"Abgeschlossene Schritte ({len(step_names)}): {', '.join(step_names)}")
                
                final_validation = result.get("final_validation")
                if final_validation:
                    is_valid = final_validation.get("is_valid", False)
                    errors = final_validation.get("errors", 0)
                    warnings = final_validation.get("warnings", 0)
                    context_parts.append(f"Validierung: is_valid={is_valid}, errors={errors}, warnings={warnings}")
        
        else:  # Tool
            context_parts.append(f"Tool '{action_name}' wurde ausgeführt.")
            context_parts.append(f"Status: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
            
            if not success:
                context_parts.append(f"Fehler: {error or stderr}")
            else:
                # Spezialfall: create_snapshot hat Metadaten (ID, Name)
                if action_name == "create_snapshot" and "snapshot_metadata" in result:
                    import json
                    metadata = result["snapshot_metadata"]
                    
                    context_parts.append(f"Snapshot erfolgreich erstellt.")
                    context_parts.append(f"Vollständige Metadaten:")
                    context_parts.append(json.dumps(metadata, indent=2, ensure_ascii=False))
                
                # Spezialfall: validate_snapshot hat strukturierte Validation-Daten
                elif action_name == "validate_snapshot" and "validation" in result:
                    validation = result["validation"]
                    is_valid = validation.get("is_valid", False)
                    errors = validation.get("errors", 0)
                    warnings = validation.get("warnings", 0)
                    
                    # KLARE Aussage für LLM: Was bedeutet is_valid?
                    if is_valid and errors == 0:
                        context_parts.append(f"✅ SNAPSHOT IST VALIDE: Der Server hat den Snapshot erfolgreich akzeptiert (isSuccessfullyValidated=true)")
                        context_parts.append(f"Validierung: errors={errors}, warnings={warnings}")
                    else:
                        context_parts.append(f"❌ SNAPSHOT IST NICHT VALIDE: Der Snapshot hat Fehler und kann nicht verwendet werden")
                        context_parts.append(f"Validierung: is_valid={is_valid}, errors={errors}, warnings={warnings}")
                    
                    # Fehler-Details
                    if errors > 0:
                        error_details = validation.get("error_details", [])
                        context_parts.append("Fehler-Details:")
                        for err in error_details:
                            context_parts.append(f"  - {err.get('message', 'Unbekannt')}")
                    
                    # Warning-Details
                    if warnings > 0:
                        warning_details = validation.get("warning_details", [])
                        context_parts.append(f"Warning-Details ({warnings} insgesamt):")
                        for warn in warning_details:
                            context_parts.append(f"  - {warn.get('message', 'Unbekannt')}")
                
                elif stdout:
                    context_parts.append(f"Output: {stdout[:500]}")
        
        result_context = "\n".join(context_parts)
        
        # LLM interpretiert das Ergebnis NATÜRLICH basierend auf User-Frage
        max_interpret_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        recent_context = ""
        if chat_history:
            recent = chat_history[-(max_interpret_pairs * 2):]
            max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
            recent_context = "\n".join([f"{m['role']}: {m['content'][:max_chars]}" for m in recent])
        
        interpret_prompt = f"""Die Benutzeranfrage war: \"{user_input}\"

{f'Bisheriger Kontext:\n{recent_context}\n' if recent_context else ''}
Du hast ein {action_type} ({action_name}) ausgeführt. Hier ist das Ergebnis:

{result_context}

KRITISCHE REGELN FÜR VALIDIERUNGS-STATUS:
- Wenn Result zeigt "✅ SNAPSHOT IST VALIDE" → Der Snapshot IST valide, antworte klar mit "Ja"
- Wenn Result zeigt "❌ SNAPSHOT IST NICHT VALIDE" → Der Snapshot IST NICHT valide
- Bei User-Frage "ist der Snapshot valide?" → BEANTWORTE MIT JA/NEIN basierend auf obigem Status
- NIEMALS nachfragen wenn die Info klar im Result steht!

WICHTIG - NUTZE DEN BISHERIGEN KONTEXT:
- Der User bezieht sich oft auf vorherige Antworten
- Bei "ja" oder "genau das" → Verstehe was gemeint ist aus dem Gesprächsverlauf
- Wenn User mehrmals "ja" sagt → Das ist eine Bestätigung, keine neue Frage!

KRITISCH - BEI BESTÄTIGUNGEN HANDELN, NICHT FRAGEN:
- "ja mach das", "okay mach", "ja bitte" → DIREKT BESTÄTIGEN, nicht nochmal fragen!
- "füge hinzu", "erstelle", "zeig mir" → HANDLUNG war bereits ausgeführt, BESTÄTIGE das Ergebnis!
- User hat bereits bestätigt → KEINE weiteren Rückfragen wie "Soll ich das für dich erledigen?"
- Bei wiederholter Bestätigung → Erkläre was BEREITS GETAN wurde, nicht was noch getan werden könnte

RESPEKTIERE DEN USER-WUNSCH:
1. Wenn User sagt "nur ja/nein", "details egal", "kurze antwort" → Gib NUR die Kernaussage (1 Satz)
2. Wenn User nach Details fragt ("was sind die warnings", "zeige fehler") → Liste ALLE Details auf
3. Sonst: Ausgewogene Antwort (2-3 Sätze, wichtigste Infos)

Erkläre das Ergebnis NATÜRLICH und KONTEXTBEZOGEN:
- Was ist das Ergebnis?
- Bei Erfolg: Wichtige Infos (z.B. Snapshot-ID, Status)
- KRITISCH bei create_snapshot: Erwähne ALLE Metadaten-Felder explizit in deiner Antwort:
  * name, id, isSuccessfullyValidated
  * So kann der User später nach jedem Feld fragen und bekommt die Info aus der Chat-History
- Bei Fehler: Was ging schief?
- Bei Warnungen: Nur erwähnen WENN User Details will oder es kritisch ist

ANTWORTE DIREKT AN DEN BENUTZER. Keine Anführungszeichen. Natürlicher Ton."""
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.interpretation_system_prompt},
                    {"role": "user", "content": interpret_prompt}
                ],
                temperature=0.7,
                max_tokens=1200  # Mehr Platz für Details bei Errors/Warnings
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"[{self.name}] Interpretation fehlgeschlagen: {e}")
            # KEIN hardcodierter Fallback - gebe technische Info zurück, App muss Error-Handling machen
            return f"[INTERPRETATION ERROR] {str(e)}"
