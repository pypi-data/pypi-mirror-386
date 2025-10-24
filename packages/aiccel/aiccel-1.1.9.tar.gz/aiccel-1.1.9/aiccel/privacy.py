import re
import uuid
import json
from typing import Dict, Any, Optional, List, Tuple

try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    GLINER_AVAILABLE = False

class EntityMasker:
    """Standalone utility for masking and unmasking sensitive entities in text before sending to agents"""
    
    def __init__(self):
        self._gliner_model = None
        self._model_loaded = False
    
    def _get_gliner_model(self):
        """Lazy load GLiNER model"""
        if not GLINER_AVAILABLE:
            raise ImportError("GLiNER is not available. Install with: pip install gliner")
        
        if self._gliner_model is None:
            print("Loading GLiNER model... (this may take a moment on first use)")
            self._gliner_model = GLiNER.from_pretrained("knowledgator/gliner-pii-edge-v1.0")
            self._model_loaded = True
            print("GLiNER model loaded successfully!")
        return self._gliner_model
    
    def mask_sensitive_entities(self, text: str, remove_email: bool = False, 
                               remove_phone: bool = False, remove_person: bool = False,
                               remove_blood_group: bool = False, remove_passport: bool = False, 
                               remove_pancard: bool = False, remove_organization: bool = False, 
                               person_threshold: float = 0.7, organization_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Mask specified sensitive entities in the text and keep a mapping for unmasking.
        
        Args:
            text: Input text to mask
            remove_email: Whether to mask email addresses
            remove_phone: Whether to mask phone numbers
            remove_person: Whether to mask person names
            remove_blood_group: Whether to mask blood group information
            remove_passport: Whether to mask passport numbers
            remove_pancard: Whether to mask PAN card numbers
            remove_organization: Whether to mask organization names
            person_threshold: Confidence threshold for person detection (0.0-1.0)
            organization_threshold: Confidence threshold for organization detection (0.0-1.0)
        
        Returns:
            Dict containing:
            - masked_text: Text with sensitive entities masked
            - mask_mapping: Dictionary mapping mask IDs to original entities
            - extracted_entities: Dictionary of all extracted entities by type
        """
        mask_mapping = {}
        entity_to_mask = {}
        extracted_entities = {
            'emails': [],
            'phones': [],
            'blood_groups': [],
            'passports': [],
            'pancards': [],
            'persons': [],
            'organizations': []
        }
        modified_text = text
        
        # Regex-based patterns
        patterns = {
            'email': {
                'pattern': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
                'prefix': 'EMAIL',
                'enabled': remove_email
            },
            'phone': {
                'pattern': r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b',
                'prefix': 'PHONE',
                'enabled': remove_phone
            },
            'blood_group': {
                'pattern': r'(?<!\w)(?:A|B|AB|O)[+-](?!\w)',
                'prefix': 'BLOOD',
                'enabled': remove_blood_group
            },
            'passport': {
                'pattern': r'\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b|\b[A-Z]{1,2}[0-9]{6,8}\b',
                'prefix': 'PASSPORT',
                'enabled': remove_passport
            },
            'pancard': {
                'pattern': r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
                'prefix': 'PAN',
                'enabled': remove_pancard
            }
        }
        
        # Step 1: Regex-based masking
        for key, meta in patterns.items():
            if meta['enabled']:
                matches = set(re.findall(meta['pattern'], modified_text))
                extracted_entities[key + 's'] = list(matches)
                for match in matches:
                    if match not in entity_to_mask:
                        mask_id = f"{meta['prefix']}_{uuid.uuid4().hex[:8]}"
                        entity_to_mask[match] = mask_id
                        mask_mapping[mask_id] = match
                    modified_text = re.sub(r'(?i)\b' + re.escape(match) + r'\b', 
                                         entity_to_mask[match], modified_text)
        
        # Step 2: GLiNER-based masking (Person, Organization)
        entity_types = []
        thresholds = {}
        
        if remove_person:
            entity_types.append("Person")
            thresholds["Person"] = person_threshold
        if remove_organization:
            entity_types.append("Organization")
            thresholds["Organization"] = organization_threshold
        
        if entity_types:
            if GLINER_AVAILABLE:
                try:
                    model = self._get_gliner_model()
                    entities = model.predict_entities(modified_text, entity_types)
                    for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
                        label = ent["label"]
                        if ent["score"] < thresholds.get(label, 0):
                            continue
                        
                        entity_text = ent["text"]
                        if entity_text.lower() not in entity_to_mask:
                            if label == "Person":
                                mask_id = f"PERSON_{uuid.uuid4().hex[:8]}"
                                extracted_entities['persons'].append(entity_text)
                            elif label == "Organization":
                                mask_id = f"ORG_{uuid.uuid4().hex[:8]}"
                                extracted_entities['organizations'].append(entity_text)
                            else:
                                continue
                            entity_to_mask[entity_text.lower()] = mask_id
                            mask_mapping[mask_id] = entity_text
                        else:
                            mask_id = entity_to_mask[entity_text.lower()]
                            if label == "Person":
                                extracted_entities['persons'].append(entity_text)
                            elif label == "Organization":
                                extracted_entities['organizations'].append(entity_text)
                        
                        # Replace in text
                        modified_text = (
                            modified_text[:ent['start']] + mask_id + modified_text[ent['end']:]
                        )
                except Exception as e:
                    print(f"Warning: GLiNER processing failed: {e}")
                    extracted_entities['gliner_error'] = str(e)
            else:
                print("Warning: GLiNER not available for person/organization detection")
                extracted_entities['gliner_warning'] = "GLiNER not available"
        
        # Normalize whitespace
        modified_text = " ".join(modified_text.split())
        
        return {
            'masked_text': modified_text,
            'mask_mapping': mask_mapping,
            'extracted_entities': extracted_entities
        }
    
    def unmask_entities(self, masked_text: str, mask_mapping: Dict[str, str]) -> str:
        """
        Restore the original entities in the text using the stored mask mapping.
        
        Args:
            masked_text: Text with masked entities
            mask_mapping: Dictionary mapping mask IDs to original entities
        
        Returns:
            Text with original entities restored
        """
        unmasked_text = masked_text
        for mask_id in sorted(mask_mapping, key=len, reverse=True):
            unmasked_text = unmasked_text.replace(mask_id, mask_mapping[mask_id])
        return " ".join(unmasked_text.split())
    
    def process_text_safely(self, text: str, agent_processor, **mask_options) -> Dict[str, Any]:
        """
        Convenience method: mask text -> process with agent -> unmask result
        
        Args:
            text: Original text with sensitive data
            agent_processor: Function/callable that processes the masked text (e.g., agent.run)
            **mask_options: Options for masking (remove_email, remove_phone, etc.)
        
        Returns:
            Dict containing:
            - original_text: Original input text
            - masked_text: Text sent to agent
            - agent_response: Raw response from agent
            - unmasked_response: Response with entities restored
            - mask_mapping: Mapping used for masking/unmasking
        """
        # Step 1: Mask the input text
        mask_result = self.mask_sensitive_entities(text, **mask_options)
        masked_text = mask_result['masked_text']
        mask_mapping = mask_result['mask_mapping']
        
        # Step 2: Process with agent
        agent_response = agent_processor(masked_text)
        
        # Step 3: Unmask the response (if it contains masked entities)
        if isinstance(agent_response, dict) and 'response' in agent_response:
            response_text = agent_response['response']
        else:
            response_text = str(agent_response)
        
        unmasked_response = self.unmask_entities(response_text, mask_mapping)
        
        return {
            'original_text': text,
            'masked_text': masked_text,
            'agent_response': agent_response,
            'unmasked_response': unmasked_response,
            'mask_mapping': mask_mapping,
            'extracted_entities': mask_result['extracted_entities']
        }


# Convenience functions for direct use
def mask_text(text: str, **options) -> Dict[str, Any]:
    """Convenience function to mask text without creating EntityMasker instance"""
    masker = EntityMasker()
    return masker.mask_sensitive_entities(text, **options)

def unmask_text(masked_text: str, mask_mapping: Dict[str, str]) -> str:
    """Convenience function to unmask text without creating EntityMasker instance"""
    masker = EntityMasker()
    return masker.unmask_entities(masked_text, mask_mapping)