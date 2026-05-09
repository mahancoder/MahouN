"""
Data Validation Module
=======================

Comprehensive data validation for legal documents.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Validation issue"""
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    location: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Validation report"""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all errors"""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all warnings"""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]
    
    @property
    def error_count(self) -> int:
        """Count of errors"""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Count of warnings"""
        return len(self.warnings)


class DataValidator:
    """
    Comprehensive data validator for legal documents
    
    Features:
    - Schema validation
    - Content validation
    - Format validation
    - Completeness checks
    - Quality checks
    """
    
    def __init__(self, strict: bool = False):
        """
        Initialize validator
        
        Args:
            strict: If True, warnings are treated as errors
        """
        self.strict = strict
        self.required_fields = {'text', 'metadata'}
        self.min_text_length = 10
        self.max_text_length = 1_000_000
    
    def validate(self, data: Dict) -> ValidationReport:
        """
        Validate data
        
        Args:
            data: Data to validate
            
        Returns:
            Validation report
        """
        report = ValidationReport(valid=True)
        
        # Schema validation
        self._validate_schema(data, report)
        
        # Content validation
        self._validate_content(data, report)
        
        # Format validation
        self._validate_format(data, report)
        
        # Quality checks
        self._validate_quality(data, report)
        
        # Determine if valid
        report.valid = len(report.errors) == 0
        if self.strict:
            report.valid = report.valid and len(report.warnings) == 0
        
        return report
    
    def _validate_schema(self, data: Dict, report: ValidationReport):
        """Validate data schema"""
        # Check required fields
        for field in self.required_fields:
            if field not in data:
                report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Missing required field: {field}",
                    field=field,
                    suggestion=f"Add '{field}' field to data"
                ))
    
    def _validate_content(self, data: Dict, report: ValidationReport):
        """Validate content"""
        if 'text' in data:
            text = data['text']
            
            # Check text length
            if len(text) < self.min_text_length:
                report.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Text too short: {len(text)} chars (min: {self.min_text_length})",
                    field='text',
                    suggestion="Provide more content"
                ))
            
            if len(text) > self.max_text_length:
                report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Text too long: {len(text)} chars (max: {self.max_text_length})",
                    field='text',
                    suggestion="Split into smaller chunks"
                ))
            
            # Check if text is empty or whitespace
            if not text.strip():
                report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="Text is empty or contains only whitespace",
                    field='text'
                ))
    
    def _validate_format(self, data: Dict, report: ValidationReport):
        """Validate data format"""
        if 'metadata' in data:
            metadata = data['metadata']
            
            # Check metadata type
            if not isinstance(metadata, dict):
                report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="Metadata must be a dictionary",
                    field='metadata'
                ))
    
    def _validate_quality(self, data: Dict, report: ValidationReport):
        """Validate data quality"""
        if 'text' in data:
            text = data['text']
            
            # Check for common issues
            if text.count('  ') > 10:
                report.issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message="Text contains multiple consecutive spaces",
                    field='text',
                    suggestion="Clean up spacing"
                ))
    
    def batch_validate(self, data_list: List[Dict]) -> List[ValidationReport]:
        """
        Validate multiple data items
        
        Args:
            data_list: List of data to validate
            
        Returns:
            List of validation reports
        """
        return [self.validate(data) for data in data_list]
    
    def is_valid(self, data: Dict) -> bool:
        """
        Quick validation check
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        report = self.validate(data)
        return report.valid
