#!/usr/bin/env python3
"""
Metadata Validator
==================
Validates document metadata for consistency and correctness
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Validation issue"""
    level: ValidationLevel
    field: str
    message: str
    value: Any = None


class MetadataValidator:
    """
    Validates legal document metadata
    
    Checks:
    - Required fields
    - Field formats
    - Value ranges
    - Cross-field consistency
    - Citation validity
    """
    
    REQUIRED_FIELDS = [
        "doc_id",
        "title",
        "doc_type",
        "text"
    ]
    
    DOC_TYPES = [
        "law",
        "regulation",
        "case",
        "article",
        "commentary"
    ]
    
    def __init__(self, strict: bool = False):
        """
        Initialize validator
        
        Args:
            strict: Fail on warnings
        """
        self.strict = strict
        log.info(f"MetadataValidator initialized (strict={strict})")
    
    def validate(self, metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate metadata
        
        Args:
            metadata: Document metadata
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check required fields
        issues.extend(self._check_required_fields(metadata))
        
        # Check field formats
        issues.extend(self._check_formats(metadata))
        
        # Check doc_type
        issues.extend(self._check_doc_type(metadata))
        
        # Check IDs
        issues.extend(self._check_ids(metadata))
        
        # Check citations
        issues.extend(self._check_citations(metadata))
        
        # Check dates
        issues.extend(self._check_dates(metadata))
        
        log.info(f"Validation complete: {len(issues)} issues found")
        return issues
    
    def _check_required_fields(self, metadata: Dict) -> List[ValidationIssue]:
        """Check required fields"""
        issues = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in metadata or not metadata[field]:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=field,
                    message=f"Required field '{field}' is missing"
                ))
        
        return issues
    
    def _check_formats(self, metadata: Dict) -> List[ValidationIssue]:
        """Check field formats"""
        issues = []
        
        # Check doc_id format
        if "doc_id" in metadata:
            doc_id = metadata["doc_id"]
            if not isinstance(doc_id, str) or len(doc_id) < 3:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field="doc_id",
                    message="doc_id must be a string with at least 3 characters",
                    value=doc_id
                ))
        
        # Check text length
        if "text" in metadata:
            text = metadata["text"]
            if len(text) < 10:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field="text",
                    message="Text is very short (< 10 characters)",
                    value=len(text)
                ))
        
        return issues
    
    def _check_doc_type(self, metadata: Dict) -> List[ValidationIssue]:
        """Check document type"""
        issues = []
        
        if "doc_type" in metadata:
            doc_type = metadata["doc_type"]
            if doc_type not in self.DOC_TYPES:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field="doc_type",
                    message=f"Unknown doc_type: {doc_type}. Expected one of {self.DOC_TYPES}",
                    value=doc_type
                ))
        
        return issues
    
    def _check_ids(self, metadata: Dict) -> List[ValidationIssue]:
        """Check ID fields"""
        issues = []
        
        # Check law_id format (if present)
        if "law_id" in metadata:
            law_id = metadata["law_id"]
            if not re.match(r'^[A-Z0-9_-]+$', str(law_id)):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field="law_id",
                    message="law_id should contain only uppercase letters, numbers, and hyphens",
                    value=law_id
                ))
        
        # Check case_id format (if present)
        if "case_id" in metadata:
            case_id = metadata["case_id"]
            if not re.match(r'^\d+$', str(case_id)):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field="case_id",
                    message="case_id should contain only numbers",
                    value=case_id
                ))
        
        return issues
    
    def _check_citations(self, metadata: Dict) -> List[ValidationIssue]:
        """Check citations"""
        issues = []
        
        if "citations" in metadata:
            citations = metadata["citations"]
            
            if not isinstance(citations, list):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field="citations",
                    message="citations must be a list"
                ))
            elif len(citations) == 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    field="citations",
                    message="No citations found"
                ))
        
        return issues
    
    def _check_dates(self, metadata: Dict) -> List[ValidationIssue]:
        """Check date fields"""
        issues = []
        
        date_fields = ["date", "publish_date", "effective_date"]
        
        for field in date_fields:
            if field in metadata:
                date_val = metadata[field]
                
                # Check format (YYYY-MM-DD)
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_val)):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        field=field,
                        message=f"{field} should be in YYYY-MM-DD format",
                        value=date_val
                    ))
        
        return issues
    
    def is_valid(self, metadata: Dict) -> bool:
        """
        Check if metadata is valid
        
        Args:
            metadata: Document metadata
            
        Returns:
            True if valid (no errors, or no warnings if strict)
        """
        issues = self.validate(metadata)
        
        if self.strict:
            # Fail on any warning or error
            return not any(
                issue.level in [ValidationLevel.ERROR, ValidationLevel.WARNING]
                for issue in issues
            )
        else:
            # Fail only on errors
            return not any(
                issue.level == ValidationLevel.ERROR
                for issue in issues
            )
    
    def generate_report(self, metadata: Dict) -> str:
        """Generate validation report"""
        issues = self.validate(metadata)
        
        if not issues:
            return "✅ Validation passed - no issues found"
        
        report = ["Validation Report", "=" * 50, ""]
        
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
        infos = [i for i in issues if i.level == ValidationLevel.INFO]
        
        if errors:
            report.append(f"❌ Errors: {len(errors)}")
            for issue in errors:
                report.append(f"  • {issue.field}: {issue.message}")
            report.append("")
        
        if warnings:
            report.append(f"⚠️  Warnings: {len(warnings)}")
            for issue in warnings:
                report.append(f"  • {issue.field}: {issue.message}")
            report.append("")
        
        if infos:
            report.append(f"ℹ️  Info: {len(infos)}")
            for issue in infos:
                report.append(f"  • {issue.field}: {issue.message}")
        
        return "\n".join(report)
