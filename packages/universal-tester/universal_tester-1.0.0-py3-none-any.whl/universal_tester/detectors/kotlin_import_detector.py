"""Enhanced Kotlin import detection system"""

import re
from typing import List, Dict, Any
from enum import Enum

class KotlinImportCategory(Enum):
    """Categories for Kotlin import detection"""
    KOTLIN_STDLIB = "kotlin_stdlib"
    COROUTINES = "coroutines"
    JUNIT = "junit"
    MOCKK = "mockk"
    KOTEST = "kotest"
    SPRING = "spring"
    JACKSON = "jackson"
    JPA = "jpa"
    ANDROID = "android"
    KTOR = "ktor"
    SERIALIZATION = "serialization"

class KotlinImportRule:
    """Kotlin import detection rule"""
    def __init__(self, patterns: List[str], imports: List[str], category: KotlinImportCategory, priority: int = 5, description: str = ""):
        self.patterns = patterns
        self.imports = imports
        self.category = category
        self.priority = priority
        self.description = description

class KotlinImportDetector:
    """Enhanced dynamic import detection system for Kotlin"""
    
    def __init__(self):
        self.rules = self._initialize_kotlin_rules()
        self.custom_rules = []
    
    def _initialize_kotlin_rules(self) -> List[KotlinImportRule]:
        """Initialize comprehensive Kotlin import detection rules"""
        return [
            # Kotlin Standard Library
            KotlinImportRule(
                patterns=[
                    r'\blistOf\s*\(',
                    r'\bmutableListOf\s*\(',
                    r'\bmapOf\s*\(',
                    r'\bmutableMapOf\s*\(',
                    r'\bsetOf\s*\(',
                    r'\bmutableSetOf\s*\(',
                    r'\.let\s*\{',
                    r'\.also\s*\{',
                    r'\.apply\s*\{',
                    r'\.run\s*\{',
                    r'\.takeIf\s*\{',
                    r'\.takeUnless\s*\{',
                ],
                imports=[
                    # Most Kotlin stdlib functions are available without explicit imports
                    # But some collection utilities might need explicit imports
                ],
                category=KotlinImportCategory.KOTLIN_STDLIB,
                priority=10,
                description="Kotlin standard library functions and collections"
            ),
            
            # Coroutines
            KotlinImportRule(
                patterns=[
                    r'\bsuspend\s+fun',
                    r'\bCoroutineScope\b',
                    r'\blaunch\s*\{',
                    r'\basync\s*\{',
                    r'\bdelay\s*\(',
                    r'\bwithContext\s*\(',
                    r'\bFlow\s*<',
                    r'\.collect\s*\{',
                    r'\.flow\s*\{',
                    r'\bChannel\s*<',
                ],
                imports=[
                    'kotlinx.coroutines.*',
                    'kotlinx.coroutines.flow.*',
                    'kotlinx.coroutines.channels.*',
                    'kotlinx.coroutines.test.*',
                ],
                category=KotlinImportCategory.COROUTINES,
                priority=9,
                description="Kotlin coroutines and flow"
            ),
            
            # JUnit 5 for Kotlin
            KotlinImportRule(
                patterns=[
                    r'@Test\b',
                    r'@BeforeEach\b',
                    r'@AfterEach\b',
                    r'@BeforeAll\b',
                    r'@AfterAll\b',
                    r'@ParameterizedTest\b',
                    r'@ExtendWith\b',
                    r'\bassertEquals\s*\(',
                    r'\bassertTrue\s*\(',
                    r'\bassertFalse\s*\(',
                    r'\bassertNotNull\s*\(',
                ],
                imports=[
                    'org.junit.jupiter.api.Test',
                    'org.junit.jupiter.api.BeforeEach',
                    'org.junit.jupiter.api.AfterEach',
                    'org.junit.jupiter.api.BeforeAll',
                    'org.junit.jupiter.api.AfterAll',
                    'org.junit.jupiter.api.Assertions.*',
                    'org.junit.jupiter.api.extension.ExtendWith',
                    'org.junit.jupiter.params.ParameterizedTest',
                    'org.junit.jupiter.params.provider.*',
                ],
                category=KotlinImportCategory.JUNIT,
                priority=9,
                description="JUnit 5 testing framework"
            ),
            
            # MockK
            KotlinImportRule(
                patterns=[
                    r'\bmockk\s*<',
                    r'\bevery\s*\{',
                    r'\bverify\s*\{',
                    r'\bcoEvery\s*\{',
                    r'\bcoVerify\s*\{',
                    r'\bspyk\s*\(',
                    r'\brelaxed\s*=\s*true',
                    r'\bmockkStatic\s*\(',
                    r'\bunmockkAll\s*\(',
                ],
                imports=[
                    'io.mockk.*',
                    'io.mockk.junit5.MockKExtension',
                ],
                category=KotlinImportCategory.MOCKK,
                priority=9,
                description="MockK mocking framework"
            ),
            
            # Kotest
            KotlinImportRule(
                patterns=[
                    r'StringSpec\s*\(',
                    r'FunSpec\s*\(',
                    r'DescribeSpec\s*\(',
                    r'BehaviorSpec\s*\(',
                    r'\bshouldBe\b',
                    r'\bshouldNotBe\b',
                    r'\bshouldContain\b',
                    r'\bshouldThrow\s*<',
                ],
                imports=[
                    'io.kotest.core.spec.style.*',
                    'io.kotest.matchers.shouldBe',
                    'io.kotest.matchers.shouldNotBe',
                    'io.kotest.matchers.collections.*',
                    'io.kotest.assertions.throwables.shouldThrow',
                ],
                category=KotlinImportCategory.KOTEST,
                priority=8,
                description="Kotest testing framework"
            ),
            
            # Spring with Kotlin
            KotlinImportRule(
                patterns=[
                    r'@RestController\b',
                    r'@Service\b',
                    r'@Repository\b',
                    r'@Component\b',
                    r'@Autowired\b',
                    r'@Value\s*\(',
                    r'@RequestMapping\b',
                    r'@GetMapping\b',
                    r'@PostMapping\b',
                ],
                imports=[
                    'org.springframework.stereotype.*',
                    'org.springframework.beans.factory.annotation.*',
                    'org.springframework.web.bind.annotation.*',
                    'org.springframework.boot.autoconfigure.*',
                ],
                category=KotlinImportCategory.SPRING,
                priority=8,
                description="Spring Framework with Kotlin"
            ),
            
            # Jackson with Kotlin
            KotlinImportRule(
                patterns=[
                    r'@JsonProperty\b',
                    r'@JsonIgnore\b',
                    r'@JsonCreator\b',
                    r'\bObjectMapper\b',
                    r'\.readValue\s*\(',
                    r'\.writeValueAsString\s*\(',
                ],
                imports=[
                    'com.fasterxml.jackson.annotation.*',
                    'com.fasterxml.jackson.databind.*',
                    'com.fasterxml.jackson.module.kotlin.*',
                ],
                category=KotlinImportCategory.JACKSON,
                priority=7,
                description="Jackson JSON processing with Kotlin module"
            ),
            
            # Kotlinx Serialization
            KotlinImportRule(
                patterns=[
                    r'@Serializable\b',
                    r'@SerialName\b',
                    r'\bJson\s*\{',
                    r'\.encodeToString\s*\(',
                    r'\.decodeFromString\s*\(',
                ],
                imports=[
                    'kotlinx.serialization.*',
                    'kotlinx.serialization.json.*',
                ],
                category=KotlinImportCategory.SERIALIZATION,
                priority=7,
                description="Kotlinx Serialization"
            ),
            
            # Ktor Framework
            KotlinImportRule(
                patterns=[
                    r'\bktor\b',
                    r'\bApplicationCall\b',
                    r'\bHttpStatusCode\b',
                    r'routing\s*\{',
                    r'get\s*\(',
                    r'post\s*\(',
                ],
                imports=[
                    'io.ktor.server.application.*',
                    'io.ktor.server.routing.*',
                    'io.ktor.server.response.*',
                    'io.ktor.http.*',
                ],
                category=KotlinImportCategory.KTOR,
                priority=7,
                description="Ktor framework"
            ),
        ]
    
    def detect_imports(self, kotlin_code: str) -> Dict[str, Any]:
        """Detect required imports based on Kotlin code patterns"""
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
                if re.search(pattern, kotlin_code, re.IGNORECASE):
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
    
    def get_contextual_imports(self, kotlin_code: str, class_name: str = None) -> List[str]:
        """Get imports with additional context-based filtering for Kotlin"""
        contextual_imports = []
        
        # Base testing imports for Kotlin
        if any(keyword in kotlin_code.lower() for keyword in ['test', '@test']):
            contextual_imports.extend([
                'org.junit.jupiter.api.Test',
                'org.junit.jupiter.api.BeforeEach',
                'org.junit.jupiter.api.Assertions.*',
                'io.mockk.*'
            ])
        
        # Coroutines context
        if any(keyword in kotlin_code for keyword in ['suspend', 'launch', 'async']):
            contextual_imports.extend([
                'kotlinx.coroutines.*',
                'kotlinx.coroutines.test.*'
            ])
        
        # Spring context
        if any(annotation in kotlin_code for annotation in ['@Service', '@Repository', '@Controller']):
            contextual_imports.extend([
                'org.springframework.stereotype.*',
                'org.springframework.beans.factory.annotation.*'
            ])
        
        # Data class context
        if 'data class' in kotlin_code:
            contextual_imports.extend([
                # Data classes typically work without additional imports
                # but might need serialization imports
            ])
        
        # Class name based context
        if class_name:
            class_lower = class_name.lower()
            
            if 'service' in class_lower:
                contextual_imports.extend([
                    'org.springframework.stereotype.Service',
                ])
            
            elif 'repository' in class_lower:
                contextual_imports.extend([
                    'org.springframework.stereotype.Repository',
                    'org.springframework.data.jpa.repository.*'
                ])
            
            elif 'controller' in class_lower:
                contextual_imports.extend([
                    'org.springframework.web.bind.annotation.*',
                    'org.springframework.http.*'
                ])
            
            elif 'test' in class_lower:
                contextual_imports.extend([
                    'org.junit.jupiter.api.*',
                    'io.mockk.*',
                    'kotlinx.coroutines.test.*'
                ])
        
        # Remove duplicates and sort
        return sorted(list(set(contextual_imports)))
    
    def add_custom_rule(self, rule: KotlinImportRule):
        """Add a custom import detection rule"""
        self.custom_rules.append(rule)

# Test function for the Kotlin import detector
def test_kotlin_import_detection():
    """Test the Kotlin import detection system"""
    detector = KotlinImportDetector()
    
    test_code = '''
package com.example.service

import kotlinx.coroutines.flow.Flow

data class User(val id: String, val name: String)

@Service
class UserService {
    
    suspend fun getUsers(): Flow<User> {
        return flow {
            emit(User("1", "John"))
        }
    }
    
    fun processUser(user: User) {
        user.let { 
            println("Processing: ${it.name}")
        }
    }
}

@ExtendWith(MockKExtension::class)
class UserServiceTest {
    
    private val mockRepository = mockk<UserRepository>()
    
    @Test
    fun `should get users`() = runTest {
        every { mockRepository.findAll() } returns listOf(testUser)
        
        val result = userService.getUsers()
        
        result shouldBe expected
        verify { mockRepository.findAll() }
    }
}
'''
    
    result = detector.detect_imports(test_code)
    
    print("🔍 Kotlin Import Detection Results:")
    print(f"Total imports detected: {len(result['detected_imports'])}")
    print(f"Rules matched: {result['total_rules_matched']}")
    print(f"Categories: {list(result['category_counts'].keys())}")
    
    for import_stmt in result['detected_imports']:
        print(f"  - {import_stmt}")

if __name__ == "__main__":
    test_kotlin_import_detection()
