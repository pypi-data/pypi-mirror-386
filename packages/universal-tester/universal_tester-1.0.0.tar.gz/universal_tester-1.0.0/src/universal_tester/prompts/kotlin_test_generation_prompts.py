"""Kotlin test generation prompts for different scenarios"""

KOTLIN_JUNIT_TEST_PROMPT = """
Generate a CLEAN, PRODUCTION-READY Kotlin JUnit test class based on detailed analysis:

📊 **Class Analysis:**
- Package: {package}
- Class: {class_name}
- Class Type: {class_type}
- Language: Kotlin
- Frameworks: {frameworks}
- Complexity Score: {complexity_score}
- Public/Internal Methods: {method_count}
- Private Methods: {private_method_count}

🎯 **Testing Strategy:**
- Approaches: {testing_approaches}
- Complexity Level: {complexity_level}
- Mocking Strategy: Use MockK for Kotlin-friendly mocking

📋 **Public/Internal Methods to Test (Direct Access):**
{methods_list}

🔒 **Private Methods (Use Reflection Only if Complex Logic):**
{private_methods_list}

🏗️ **Available Constructors:**
{constructors_list}

🔗 **Kotlin Test Imports Needed:**
```kotlin
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.extension.ExtendWith
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.ValueSource
import io.mockk.*
import io.mockk.junit5.MockKExtension
import kotlinx.coroutines.test.*
import kotlinx.coroutines.runBlocking
// Add other imports as needed based on the class being tested
```

🚨 **CRITICAL KOTLIN TESTING RULES:**

**MOCKK USAGE (Kotlin-specific):**
- Use `mockk<ClassName>()` instead of Mockito annotations
- Use `every {{ mock.method() }} returns value` for stubbing
- Use `verify {{ mock.method() }}` for verification
- Use `coEvery {{ mock.suspendFunction() }} returns value` for suspend functions
- Use `coVerify {{ mock.suspendFunction() }}` for suspend function verification

**COROUTINES TESTING:**
- For suspend functions: Use `runTest {{ }}` or `runBlocking {{ }}`
- Use `TestScope` and `TestDispatcher` for advanced coroutine testing
- Use `coEvery` and `coVerify` for suspend function mocking

**KOTLIN NULL SAFETY:**
- Handle nullable types properly: `String?`, `List<String>?`
- Use `assertNotNull()` before accessing nullable properties
- Test both null and non-null scenarios for nullable parameters

**DATA CLASS TESTING:**
- Test `equals()`, `hashCode()`, and `toString()` for data classes
- Test `copy()` function with different parameter combinations
- Test component functions (`component1()`, `component2()`, etc.)

**PROPERTY TESTING:**
- Test both getter and setter for mutable properties (`var`)
- Test immutable properties (`val`) initialization
- Test custom getters and setters if present

**OBJECT/SINGLETON TESTING:**
- For `object` classes, test static behavior
- Use direct class reference for object instances

**EXTENSION FUNCTION TESTING:**
- Test extension functions with various receiver types
- Test null receiver scenarios for nullable extension functions

Generate a complete Kotlin JUnit 5 test class with:
- Proper package declaration
- **COMPREHENSIVE imports including ALL required classes**
- @ExtendWith(MockKExtension::class)
- MockK mocks using `mockk<Type>()`
- @BeforeEach setup method
- Multiple @Test methods for each PUBLIC/INTERNAL method
- Coroutine testing for suspend functions
- Parameterized tests where appropriate
- Null safety testing
- Data class specific tests (if applicable)

**Kotlin Test Class Example Structure:**
```kotlin
package {package}

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.extension.ExtendWith
import org.junit.jupiter.api.Assertions.*
import io.mockk.*
import io.mockk.junit5.MockKExtension
import kotlinx.coroutines.test.runTest

@ExtendWith(MockKExtension::class)
class {class_name}Test {{

    private lateinit var objectUnderTest: {class_name}
    
    // MockK mocks
    private val mockDependency = mockk<DependencyType>()

    @BeforeEach
    fun setUp() {{
        objectUnderTest = {class_name}(mockDependency)
    }}

    @Test
    fun `test method name with descriptive scenario`() {{
        // Given
        every {{ mockDependency.method() }} returns "expectedValue"
        
        // When
        val result = objectUnderTest.methodToTest()
        
        // Then
        assertEquals("expectedValue", result)
        verify {{ mockDependency.method() }}
    }}

    // For suspend functions
    @Test
    fun `test suspend function`() = runTest {{
        // Given
        coEvery {{ mockDependency.suspendMethod() }} returns "result"
        
        // When
        val result = objectUnderTest.suspendMethodToTest()
        
        // Then
        assertEquals("result", result)
        coVerify {{ mockDependency.suspendMethod() }}
    }}
}}
```

OUTPUT FORMAT: Return ONLY the complete Kotlin test class code.
"""

KOTLIN_KOTEST_PROMPT = """
Generate a CLEAN Kotest-style test class for Kotlin:

📊 **Class Analysis:**
- Package: {package}
- Class: {class_name}
- Class Type: {class_type}
- Language: Kotlin
- Frameworks: {frameworks}

🔗 **Kotest Imports:**
```kotlin
import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe
import io.kotest.matchers.collections.shouldContain
import io.mockk.*
```

**Kotest Testing Pattern:**
```kotlin
class {class_name}Test : StringSpec({{
    
    "should test basic functionality" {{
        // Given
        val objectUnderTest = {class_name}()
        
        // When
        val result = objectUnderTest.method()
        
        // Then
        result shouldBe "expected"
    }}
    
    "should handle null values properly" {{
        // Test null safety
    }}
    
    "should test suspend functions" {{
        // Coroutine testing
    }}
}})
```

OUTPUT FORMAT: Return ONLY the complete Kotest test class code.
"""

def get_kotlin_test_prompt(test_framework: str = "junit") -> str:
    """Get appropriate Kotlin test prompt based on framework choice"""
    if test_framework.lower() == "kotest":
        return KOTLIN_KOTEST_PROMPT
    else:
        return KOTLIN_JUNIT_TEST_PROMPT
