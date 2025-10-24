#!/usr/bin/env python3
"""
Enhanced Dynamic Import Detection System
Automatically detects and handles required dependencies based on code patterns
"""

import re
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class ImportCategory(Enum):
    """Categories of imports for better organization"""
    SERVLET = "servlet"
    SPRING = "spring"
    JACKSON = "jackson"
    COLLECTIONS = "collections"
    REFLECTION = "reflection"
    IO = "io"
    CONCURRENT = "concurrent"
    TIME = "time"
    REGEX = "regex"
    NETWORK = "network"
    DATABASE = "database"
    VALIDATION = "validation"
    LOGGING = "logging"
    TESTING = "testing"
    EXCEPTION = "exception"
    UTILITY = "utility"

@dataclass
class ImportRule:
    """Represents a rule for detecting when an import is needed"""
    patterns: List[str]  # Code patterns to match
    imports: List[str]   # Required imports when pattern matches
    category: ImportCategory
    priority: int = 1    # Higher priority imports are added first
    description: str = ""

class DynamicImportDetector:
    """Enhanced dynamic import detection system"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.custom_rules = []
    
    def _initialize_rules(self) -> List[ImportRule]:
        """Initialize comprehensive import detection rules"""
        rules = [
            # Servlet API patterns
            ImportRule(
                patterns=[
                    r'HttpServletRequest\s+\w+',
                    r'ServletRequest\s+\w+',
                    r'\.getHeaderNames\(\)',
                    r'\.getParameterNames\(\)',
                    r'\.getHeaders\(\w+\)',
                    r'Enumeration<[^>]+>\s+\w+\s*=\s*\w+\.get\w+Names\(\)'
                ],
                imports=[
                    'java.util.Enumeration',
                    'jakarta.servlet.http.HttpServletRequest',
                    'jakarta.servlet.http.HttpServletResponse',
                    'jakarta.servlet.ServletRequest',
                    'jakarta.servlet.ServletResponse'
                ],
                category=ImportCategory.SERVLET,
                priority=10,
                description="Servlet API and related HTTP request/response handling"
            ),
            
            # Spring Framework patterns
            ImportRule(
                patterns=[
                    r'HttpHeaders\s+\w+',
                    r'ResponseEntity\s*<[^>]*>',
                    r'HttpStatus\.\w+',
                    r'@RestController',
                    r'@RequestMapping',
                    r'@GetMapping',
                    r'@PostMapping',
                    r'@PutMapping',
                    r'@DeleteMapping',
                    r'@Autowired',
                    r'@Service',
                    r'@Component',
                    r'@Repository'
                ],
                imports=[
                    'org.springframework.http.HttpHeaders',
                    'org.springframework.http.ResponseEntity',
                    'org.springframework.http.HttpStatus',
                    'org.springframework.web.bind.annotation.RestController',
                    'org.springframework.web.bind.annotation.RequestMapping',
                    'org.springframework.beans.factory.annotation.Autowired',
                    'org.springframework.stereotype.Service',
                    'org.springframework.stereotype.Component',
                    'org.springframework.stereotype.Repository'
                ],
                category=ImportCategory.SPRING,
                priority=9,
                description="Spring Framework annotations and HTTP utilities"
            ),
            
            # Jackson JSON processing
            ImportRule(
                patterns=[
                    r'ObjectMapper\s+\w+',
                    r'JsonNode\s+\w+',
                    r'\.readTree\(',
                    r'\.writeValueAsString\(',
                    r'\.readValue\(',
                    r'@JsonProperty',
                    r'@JsonIgnore',
                    r'JsonProcessingException'
                ],
                imports=[
                    'com.fasterxml.jackson.databind.ObjectMapper',
                    'com.fasterxml.jackson.databind.JsonNode',
                    'com.fasterxml.jackson.core.JsonProcessingException',
                    'com.fasterxml.jackson.annotation.JsonProperty',
                    'com.fasterxml.jackson.annotation.JsonIgnore'
                ],
                category=ImportCategory.JACKSON,
                priority=8,
                description="Jackson JSON processing and annotations"
            ),
            
            # Stream and Collections
            ImportRule(
                patterns=[
                    r'\.stream\(\)',
                    r'\.collect\(',
                    r'Collectors\.\w+',
                    r'Stream\s*<[^>]*>',
                    r'\.filter\(',
                    r'\.map\(',
                    r'\.forEach\(',
                    r'\.reduce\(',
                    r'\.flatMap\(',
                    r'\.distinct\(\)',
                    r'\.sorted\(',
                    r'\.limit\(',
                    r'\.skip\('
                ],
                imports=[
                    'java.util.stream.Stream',
                    'java.util.stream.Collectors',
                    'java.util.stream.IntStream',
                    'java.util.stream.LongStream',
                    'java.util.stream.DoubleStream',
                    'java.util.function.Function',
                    'java.util.function.Predicate',
                    'java.util.function.Consumer'
                ],
                category=ImportCategory.COLLECTIONS,
                priority=7,
                description="Stream API and functional programming utilities"
            ),
            
            # Reflection patterns
            ImportRule(
                patterns=[
                    r'Method\s+\w+',
                    r'Field\s+\w+',
                    r'\.setAccessible\(',
                    r'\.getDeclaredMethods\(\)',
                    r'\.getDeclaredFields\(\)',
                    r'\.invoke\(',
                    r'\.get\(\w+\)',
                    r'\.set\(\w+,',
                    r'Class\.forName\(',
                    r'\.getClass\(\)',
                    r'\.newInstance\(\)'
                ],
                imports=[
                    'java.lang.reflect.Method',
                    'java.lang.reflect.Field',
                    'java.lang.reflect.Constructor',
                    'java.lang.reflect.InvocationTargetException',
                    'java.lang.reflect.Modifier',
                    'java.lang.ClassNotFoundException',
                    'java.lang.InstantiationException',
                    'java.lang.IllegalAccessException'
                ],
                category=ImportCategory.REFLECTION,
                priority=6,
                description="Java reflection API"
            ),
            
            # I/O patterns
            ImportRule(
                patterns=[
                    r'InputStream\s+\w+',
                    r'OutputStream\s+\w+',
                    r'ByteArrayInputStream\s+\w+',
                    r'FileInputStream\s+\w+',
                    r'InputStreamReader\s+\w+',
                    r'BufferedReader\s+\w+',
                    r'FileReader\s+\w+',
                    r'PrintWriter\s+\w+',
                    r'IOException',
                    r'Files\.\w+',
                    r'Path\s+\w+',
                    r'Paths\.get\('
                ],
                imports=[
                    'java.io.InputStream',
                    'java.io.OutputStream',
                    'java.io.ByteArrayInputStream',
                    'java.io.FileInputStream',
                    'java.io.InputStreamReader',
                    'java.io.BufferedReader',
                    'java.io.FileReader',
                    'java.io.PrintWriter',
                    'java.io.IOException',
                    'java.nio.file.Files',
                    'java.nio.file.Path',
                    'java.nio.file.Paths'
                ],
                category=ImportCategory.IO,
                priority=5,
                description="Input/Output operations and file handling"
            ),
            
            # Concurrent programming
            ImportRule(
                patterns=[
                    r'CompletableFuture\s*<[^>]*>',
                    r'ExecutorService\s+\w+',
                    r'ThreadPoolExecutor\s+\w+',
                    r'Future\s*<[^>]*>',
                    r'TimeUnit\.\w+',
                    r'@Async',
                    r'CountDownLatch\s+\w+',
                    r'ConcurrentHashMap\s*<[^>]*>',
                    r'AtomicInteger\s+\w+',
                    r'AtomicLong\s+\w+',
                    r'ReentrantLock\s+\w+'
                ],
                imports=[
                    'java.util.concurrent.CompletableFuture',
                    'java.util.concurrent.ExecutorService',
                    'java.util.concurrent.ThreadPoolExecutor',
                    'java.util.concurrent.Future',
                    'java.util.concurrent.TimeUnit',
                    'java.util.concurrent.CountDownLatch',
                    'java.util.concurrent.ConcurrentHashMap',
                    'java.util.concurrent.atomic.AtomicInteger',
                    'java.util.concurrent.atomic.AtomicLong',
                    'java.util.concurrent.locks.ReentrantLock'
                ],
                category=ImportCategory.CONCURRENT,
                priority=4,
                description="Concurrent programming utilities"
            ),
            
            # Time and Date
            ImportRule(
                patterns=[
                    r'LocalDateTime\s+\w+',
                    r'LocalDate\s+\w+',
                    r'LocalTime\s+\w+',
                    r'Instant\s+\w+',
                    r'ZonedDateTime\s+\w+',
                    r'DateTimeFormatter\s+\w+',
                    r'Duration\s+\w+',
                    r'Period\s+\w+',
                    r'\.now\(\)',
                    r'\.parse\(',
                    r'\.format\(',
                    r'\.ofPattern\('
                ],
                imports=[
                    'java.time.LocalDateTime',
                    'java.time.LocalDate',
                    'java.time.LocalTime',
                    'java.time.Instant',
                    'java.time.ZonedDateTime',
                    'java.time.format.DateTimeFormatter',
                    'java.time.Duration',
                    'java.time.Period',
                    'java.time.ZoneId',
                    'java.time.temporal.ChronoUnit'
                ],
                category=ImportCategory.TIME,
                priority=3,
                description="Modern Java time API"
            ),
            
            # Regular expressions
            ImportRule(
                patterns=[
                    r'Pattern\s+\w+',
                    r'Matcher\s+\w+',
                    r'Pattern\.compile\(',
                    r'\.matcher\(',
                    r'\.matches\(',
                    r'\.find\(\)',
                    r'\.group\(',
                    r'\.replaceAll\(',
                    r'\.split\('
                ],
                imports=[
                    'java.util.regex.Pattern',
                    'java.util.regex.Matcher',
                    'java.util.regex.PatternSyntaxException'
                ],
                category=ImportCategory.REGEX,
                priority=2,
                description="Regular expression utilities"
            ),
            
            # Network operations
            ImportRule(
                patterns=[
                    r'URL\s+\w+',
                    r'URI\s+\w+',
                    r'HttpURLConnection\s+\w+',
                    r'URLConnection\s+\w+',
                    r'MalformedURLException',
                    r'URISyntaxException',
                    r'Socket\s+\w+',
                    r'ServerSocket\s+\w+',
                    r'InetAddress\s+\w+'
                ],
                imports=[
                    'java.net.URL',
                    'java.net.URI',
                    'java.net.HttpURLConnection',
                    'java.net.URLConnection',
                    'java.net.MalformedURLException',
                    'java.net.URISyntaxException',
                    'java.net.Socket',
                    'java.net.ServerSocket',
                    'java.net.InetAddress'
                ],
                category=ImportCategory.NETWORK,
                priority=1,
                description="Network programming utilities"
            ),
            
            # Exception handling
            ImportRule(
                patterns=[
                    r'throw\s+new\s+\w+Exception',
                    r'throws\s+\w+Exception',
                    r'catch\s*\(\s*\w+Exception',
                    r'RuntimeException\s+\w+',
                    r'IllegalArgumentException\s+\w+',
                    r'IllegalStateException\s+\w+',
                    r'UnsupportedOperationException\s+\w+'
                ],
                imports=[
                    'java.lang.Exception',
                    'java.lang.RuntimeException',
                    'java.lang.IllegalArgumentException',
                    'java.lang.IllegalStateException',
                    'java.lang.UnsupportedOperationException',
                    'java.lang.NullPointerException',
                    'java.lang.IndexOutOfBoundsException'
                ],
                category=ImportCategory.EXCEPTION,
                priority=1,
                description="Exception handling classes"
            ),
            
            # Utility classes
            ImportRule(
                patterns=[
                    r'Optional\s*<[^>]*>',
                    r'Optional\s+\w+',
                    r'\.of\(',
                    r'\.ofNullable\(',
                    r'\.orElse\(',
                    r'\.orElseGet\(',
                    r'\.isPresent\(\)',
                    r'\.isEmpty\(\)',
                    r'Arrays\.\w+',
                    r'Collections\.\w+',
                    r'Objects\.\w+',
                    r'StringUtils\.\w+'
                ],
                imports=[
                    'java.util.Optional',
                    'java.util.Arrays',
                    'java.util.Collections',
                    'java.util.Objects',
                    'java.util.StringJoiner',
                    'java.util.UUID',
                    'java.util.Base64'
                ],
                category=ImportCategory.UTILITY,
                priority=1,
                description="Common utility classes"
            )
        ]
        
        return rules
    
    def add_custom_rule(self, rule: ImportRule):
        """Add a custom import rule"""
        self.custom_rules.append(rule)
    
    def detect_imports(self, java_code: str) -> Dict[str, Any]:
        """Detect required imports based on code patterns"""
        detected_imports = set()
        matched_rules = []
        category_counts = {}
        
        # Combine default and custom rules
        all_rules = self.rules + self.custom_rules
        
        # Sort rules by priority (higher priority first)
        all_rules.sort(key=lambda r: r.priority, reverse=True)
        
        for rule in all_rules:
            matches = []
            for pattern in rule.patterns:
                if re.search(pattern, java_code, re.IGNORECASE):
                    matches.append(pattern)
            
            if matches:
                # Add all imports from this rule
                for import_stmt in rule.imports:
                    detected_imports.add(import_stmt)
                
                # Track rule matching
                matched_rules.append({
                    'rule': rule,
                    'matched_patterns': matches
                })
                
                # Count by category
                category_counts[rule.category.value] = category_counts.get(rule.category.value, 0) + 1
        
        return {
            'detected_imports': sorted(list(detected_imports)),
            'matched_rules': matched_rules,
            'category_counts': category_counts,
            'total_rules_matched': len(matched_rules)
        }
    
    def get_contextual_imports(self, java_code: str, class_name: str = None) -> List[str]:
        """Get imports with additional context-based filtering"""
        detection_result = self.detect_imports(java_code)
        detected_imports = detection_result['detected_imports']
        
        # Context-based filtering
        contextual_imports = []
        
        # Add base imports
        contextual_imports.extend(detected_imports)
        
        # Add context-specific imports based on class name
        if class_name:
            class_lower = class_name.lower()
            
            if 'controller' in class_lower:
                contextual_imports.extend([
                    'org.springframework.web.bind.annotation.RestController',
                    'org.springframework.web.bind.annotation.RequestMapping',
                    'org.springframework.http.ResponseEntity'
                ])
            
            elif 'service' in class_lower:
                contextual_imports.extend([
                    'org.springframework.stereotype.Service',
                    'org.springframework.beans.factory.annotation.Autowired'
                ])
            
            elif 'repository' in class_lower or 'dao' in class_lower:
                contextual_imports.extend([
                    'org.springframework.stereotype.Repository',
                    'org.springframework.data.jpa.repository.JpaRepository'
                ])
            
            elif 'validator' in class_lower:
                contextual_imports.extend([
                    'jakarta.validation.Valid',
                    'jakarta.validation.constraints.NotNull',
                    'jakarta.validation.constraints.NotEmpty'
                ])
            
            elif 'test' in class_lower:
                contextual_imports.extend([
                    'org.junit.jupiter.api.Test',
                    'org.junit.jupiter.api.BeforeEach',
                    'org.mockito.Mock',
                    'org.mockito.InjectMocks'
                ])
        
        # Remove duplicates and sort
        return sorted(list(set(contextual_imports)))
    
    def generate_import_report(self, java_code: str) -> str:
        """Generate a detailed report of detected imports"""
        detection_result = self.detect_imports(java_code)
        
        report = "🔍 Dynamic Import Detection Report\n"
        report += "=" * 50 + "\n\n"
        
        report += f"📊 Total imports detected: {len(detection_result['detected_imports'])}\n"
        report += f"🎯 Rules matched: {detection_result['total_rules_matched']}\n\n"
        
        # Category breakdown
        if detection_result['category_counts']:
            report += "📋 Category Breakdown:\n"
            for category, count in detection_result['category_counts'].items():
                report += f"  • {category.title()}: {count} rules\n"
            report += "\n"
        
        # Detected imports by category
        imports_by_category = {}
        for rule_info in detection_result['matched_rules']:
            category = rule_info['rule'].category.value
            if category not in imports_by_category:
                imports_by_category[category] = []
            imports_by_category[category].extend(rule_info['rule'].imports)
        
        for category, imports in imports_by_category.items():
            report += f"📦 {category.title()} Imports:\n"
            for imp in sorted(set(imports)):
                report += f"  • {imp}\n"
            report += "\n"
        
        return report

# Example usage and testing
def test_enhanced_dynamic_detection():
    """Test the enhanced dynamic import detection system"""
    detector = DynamicImportDetector()
    
    test_code = '''
package com.example.web;

import jakarta.servlet.http.HttpServletRequest;

public class RequestProcessor {
    private ObjectMapper objectMapper = new ObjectMapper();
    
    public void processRequest(HttpServletRequest request) {
        // Servlet operations
        Enumeration<String> headerNames = request.getHeaderNames();
        
        // Jackson operations
        JsonNode node = objectMapper.readTree(jsonString);
        
        // Stream operations
        List<String> results = items.stream()
            .filter(item -> item.length() > 0)
            .collect(Collectors.toList());
        
        // Reflection
        Method method = clazz.getDeclaredMethod("test");
        method.setAccessible(true);
        
        // URL operations
        URL url = new URL("http://example.com");
        Pattern pattern = Pattern.compile("^https?://.*");
        
        // Time operations
        LocalDateTime now = LocalDateTime.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        
        // Concurrent operations
        CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> "test");
        
        // Optional operations
        Optional<String> optional = Optional.ofNullable(getValue());
    }
}
    '''
    
    # Test detection
    result = detector.detect_imports(test_code)
    
    print("🧪 Enhanced Dynamic Import Detection Test")
    print("=" * 50)
    print(f"📊 Total imports detected: {len(result['detected_imports'])}")
    print(f"🎯 Rules matched: {result['total_rules_matched']}")
    
    print("\n📋 Detected Imports:")
    for imp in result['detected_imports']:
        print(f"  • {imp}")
    
    print("\n📊 Category Breakdown:")
    for category, count in result['category_counts'].items():
        print(f"  • {category.title()}: {count} rules")
    
    # Generate detailed report
    report = detector.generate_import_report(test_code)
    print("\n" + report)
    
    return len(result['detected_imports']) > 20  # Should detect many imports

if __name__ == "__main__":
    test_enhanced_dynamic_detection()
