"""Data extraction, classification, and labeling pipeline for call transcripts."""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import yaml
import openai
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models import CallExtractedData

logger = logging.getLogger(__name__)


class CallDataPipeline:
    """Pipeline for extracting, classifying, and labeling call data from transcripts."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.prompts_config = self._load_prompts_config()
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def _load_prompts_config(self) -> Dict[str, Any]:
        """Load prompts configuration from YAML file."""
        try:
            with open("config/agent_prompts.yaml", "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts config: {e}")
            return {}
    
    async def process_call_transcript(self, call_id: str, transcript: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Process a call transcript through the complete pipeline.
        
        Args:
            call_id: Unique identifier for the call
            transcript: Call transcript data
            db: Database session
            
        Returns:
            Dictionary containing all processing results
        """
        # Create or get existing extracted data record
        extracted_data_record = db.query(CallExtractedData).filter(
            CallExtractedData.call_id == call_id
        ).first()
        
        if not extracted_data_record:
            extracted_data_record = CallExtractedData(
                id=str(uuid.uuid4()),
                call_id=call_id,
                processing_status="processing"
            )
            db.add(extracted_data_record)
            db.commit()
            db.refresh(extracted_data_record)
        else:
            extracted_data_record.processing_status = "processing"
            db.commit()
        
        try:
            # Convert transcript to string for prompt processing
            transcript_text = self._transcript_to_text(transcript)
            
            # Debug: Log the transcript text
            logger.info(f"Transcript text length: {len(transcript_text)}")
            logger.info(f"Transcript preview: {transcript_text[:200]}...")
            
            # Run all processing tasks in parallel
            extraction_task = self._run_extraction(transcript_text)
            classification_task = self._run_classification(transcript_text)
            labeling_task = self._run_labeling(transcript_text)
            
            # Wait for all tasks to complete
            extraction_results, classification_results, labeling_results = await asyncio.gather(
                extraction_task, classification_task, labeling_task,
                return_exceptions=True
            )
            
            # Process results and handle exceptions
            final_results = {
                "extraction_data": self._process_extraction_results(extraction_results),
                "classification_data": self._process_classification_results(classification_results),
                "labeling_data": self._process_labeling_results(labeling_results),
                "processing_errors": self._collect_errors([extraction_results, classification_results, labeling_results])
            }
            
            # Update database record
            extracted_data_record.extraction_data = final_results["extraction_data"]
            extracted_data_record.classification_data = final_results["classification_data"]
            extracted_data_record.labeling_data = final_results["labeling_data"]
            extracted_data_record.processing_errors = final_results["processing_errors"]
            extracted_data_record.processing_status = "completed"
            extracted_data_record.updated_at = db.query(func.now()).scalar()
            
            db.commit()
            
            logger.info(f"Successfully processed call {call_id}")
            return final_results
            
        except Exception as e:
            logger.error(f"Failed to process call {call_id}: {e}")
            extracted_data_record.processing_status = "failed"
            extracted_data_record.processing_errors = {"pipeline_error": str(e)}
            db.commit()
            raise
    
    def _transcript_to_text(self, transcript: Dict[str, Any]) -> str:
        """Convert transcript JSON to readable text."""
        try:
            if isinstance(transcript, dict):
                if "segments" in transcript:
                    # Format with timestamps and speakers
                    text_parts = []
                    for segment in transcript["segments"]:
                        speaker = segment.get("speaker", "Unknown")
                        text = segment.get("text", "")
                        start_time = segment.get("start", 0)
                        text_parts.append(f"[{start_time:.1f}s] {speaker}: {text}")
                    return "\n".join(text_parts)
                elif "text" in transcript:
                    return transcript["text"]
                else:
                    return json.dumps(transcript, indent=2)
            else:
                return str(transcript)
        except Exception as e:
            logger.warning(f"Error converting transcript to text: {e}")
            return str(transcript)
    
    async def _run_extraction(self, transcript_text: str) -> Dict[str, Any]:
        """Run all extraction prompts in parallel."""
        extraction_config = self.prompts_config.get("extraction", {})
        if not extraction_config:
            return {"error": "No extraction prompts configured"}
        
        tasks = []
        for extraction_name, extraction_data in extraction_config.items():
            if "prompt" in extraction_data:
                task = self._run_single_extraction(extraction_name, extraction_data["prompt"], transcript_text)
                tasks.append(task)
        
        if not tasks:
            return {"error": "No valid extraction prompts found"}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        for i, (extraction_name, _) in enumerate(extraction_config.items()):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    combined_results[extraction_name] = {"error": str(result)}
                else:
                    combined_results[extraction_name] = result
        
        return combined_results
    
    async def _run_classification(self, transcript_text: str) -> Dict[str, Any]:
        """Run all classification prompts in parallel."""
        classification_config = self.prompts_config.get("classification", {})
        if not classification_config:
            return {"error": "No classification prompts configured"}
        
        tasks = []
        for classification_name, classification_data in classification_config.items():
            if "prompt" in classification_data:
                task = self._run_single_classification(classification_name, classification_data["prompt"], transcript_text)
                tasks.append(task)
        
        if not tasks:
            return {"error": "No valid classification prompts found"}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        for i, (classification_name, _) in enumerate(classification_config.items()):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    combined_results[classification_name] = {"error": str(result)}
                else:
                    combined_results[classification_name] = result
        
        return combined_results
    
    async def _run_labeling(self, transcript_text: str) -> Dict[str, Any]:
        """Run all labeling prompts in parallel."""
        labeling_config = self.prompts_config.get("labeling", [])
        if not labeling_config:
            return {"error": "No labeling prompts configured"}
        
        tasks = []
        for label_config in labeling_config:
            if "label" in label_config and "prompt" in label_config:
                task = self._run_single_labeling(label_config["label"], label_config["prompt"], transcript_text)
                tasks.append(task)
        
        if not tasks:
            return {"error": "No valid labeling prompts found"}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        for i, label_config in enumerate(labeling_config):
            if i < len(results):
                result = results[i]
                label_name = label_config["label"]
                if isinstance(result, Exception):
                    combined_results[label_name] = {"error": str(result)}
                else:
                    combined_results[label_name] = result
        
        return combined_results
    
    async def _run_single_extraction(self, extraction_name: str, prompt: str, transcript_text: str) -> Dict[str, Any]:
        """Run a single extraction prompt."""
        try:
            formatted_prompt = prompt.format(transcript=transcript_text)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using the cheapest model as requested
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Extract structured data from call transcripts and return only valid JSON. Always return complete, valid JSON objects."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Debug: Log the actual response
            logger.info(f"Raw response for {extraction_name}: {repr(content)}")
            
            # Check if response was truncated
            if response.choices[0].finish_reason == "length":
                logger.warning(f"Response was truncated for {extraction_name}")
                return {"error": f"Response was truncated: {content}"}
            
            # Try to parse JSON from response
            try:
                # First try to parse the content directly
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass
                
                # If that fails, try to extract JSON from the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    # Clean up any extra whitespace or newlines
                    json_content = json_content.strip()
                    return json.loads(json_content)
                else:
                    # Log the content for debugging
                    logger.error(f"No JSON braces found in response for {extraction_name}: {repr(content)}")
                    return {"error": f"Could not extract JSON from response: {content}"}
            except json.JSONDecodeError as e:
                # Log the content for debugging
                logger.error(f"JSON parsing failed for {extraction_name}: {repr(content)}")
                logger.error(f"JSON error: {e}")
                return {"error": f"Invalid JSON response: {content}. Error: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in extraction {extraction_name}: {e}")
            return {"error": str(e)}
    
    async def _run_single_classification(self, classification_name: str, prompt: str, transcript_text: str) -> str:
        """Run a single classification prompt."""
        try:
            formatted_prompt = prompt.format(transcript=transcript_text)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using the cheapest model as requested
                messages=[
                    {"role": "system", "content": "You are a classification assistant. Classify call transcripts into predefined categories. Return only the category name."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"Error in classification {classification_name}: {e}")
            return f"error: {str(e)}"
    
    async def _run_single_labeling(self, label_name: str, prompt: str, transcript_text: str) -> bool:
        """Run a single labeling prompt."""
        try:
            formatted_prompt = prompt.format(transcript=transcript_text)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using the cheapest model as requested
                messages=[
                    {"role": "system", "content": "You are a labeling assistant. Determine if a call should have specific labels. Return only 'yes' or 'no'."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().lower()
            return result == "yes"
                
        except Exception as e:
            logger.error(f"Error in labeling {label_name}: {e}")
            return False
    
    def _process_extraction_results(self, results: Any) -> Dict[str, Any]:
        """Process extraction results and handle exceptions."""
        if isinstance(results, Exception):
            return {"error": str(results)}
        return results
    
    def _process_classification_results(self, results: Any) -> Dict[str, Any]:
        """Process classification results and handle exceptions."""
        if isinstance(results, Exception):
            return {"error": str(results)}
        return results
    
    def _process_labeling_results(self, results: Any) -> Dict[str, Any]:
        """Process labeling results and handle exceptions."""
        if isinstance(results, Exception):
            return {"error": str(results)}
        return results
    
    def _collect_errors(self, results_list: List[Any]) -> Dict[str, str]:
        """Collect all errors from processing results."""
        errors = {}
        for i, results in enumerate(results_list):
            if isinstance(results, Exception):
                errors[f"task_{i}"] = str(results)
            elif isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, dict) and "error" in value:
                        errors[key] = value["error"]
        return errors


# Global pipeline instance
pipeline = CallDataPipeline()
