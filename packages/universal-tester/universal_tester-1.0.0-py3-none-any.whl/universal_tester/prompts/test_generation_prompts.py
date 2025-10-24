"""Test generation prompts for different scenarios"""

ENHANCED_JUNIT_WITH_FILES_PROMPT = """
Generate a CLEAN, PRODUCTION-READY JUnit test class with optional file integration based on detailed analysis:

📊 **Class Analysis:**
- Package: {package}
- Class: {class_name}
- Frameworks: {frameworks}
- Complexity Score: {complexity_score}
- Public/Protected Methods: {method_count}
- Private Methods: {private_method_count}

🎯 **Testing Strategy:**
- Approaches: {testing_approaches}
- Complexity Level: {complexity_level}
- Mocking Strategy: {mocking_strategy}

{file_context}

{config_context}

📋 **Public/Protected Methods to Test (Direct Access):**
{methods_list}

🔒 **Private Methods (Use Reflection Only if Complex Logic):**
{private_methods_list}

🏗️ **Available Constructors (CRITICAL - Use complete signatures for object creation):**
{constructors_list}

🔗 **Common Test Imports Needed:**
{import_guidance}

⚠️ **Method Validation Guidelines:**
{method_validation}

🚨 **CRITICAL TYPE SAFETY RULES - PREVENT COMPILATION ERRORS:**

**STRING vs LIST TYPE SAFETY:**
- **ALWAYS check method parameter types before creating test data**
- **If method expects String parameter**: Use `"test string"` 
- **If method expects List<String> parameter**: Use `Arrays.asList("item1", "item2")` or `List.of("item1", "item2")`
- **If method expects Collection parameter**: Use appropriate collection type
- **NEVER pass String where List is expected**
- **NEVER pass List where String is expected**

🚨 **CRITICAL LOGGERBEAN TYPE CONVERSION RULES:**

**LOGGERBEAN SETTER COMPILATION ERROR PREVENTION:**
LoggerBean is a common source of "incompatible types" compilation errors due to mixed parameter types:

**LOGGERBEAN STRING SETTERS (expect String parameter):**
- `setChannelId("WEB_APP")` - expects String
- `setCorrelationId("12345")` - expects String  
- `setUserId("user123")` - expects String
- `setRequestId("req456")` - expects String

**LOGGERBEAN LIST SETTERS (expect List<String> parameter):**
- `setTransactionType(Arrays.asList("SALE"))` - expects List<String>
- `setProductCategories(Arrays.asList("category1", "category2"))` - expects List<String>
- **ALWAYS use Arrays.asList() for List<String> parameters**

**CRITICAL LOGGERBEAN RULES:**
❌ NEVER: `loggerBean.setTransactionType("TYPE")` - causes compilation error
✅ ALWAYS: `loggerBean.setTransactionType(Arrays.asList("TYPE"))` - correct List<String>
❌ NEVER: `loggerBean.setChannelId(Arrays.asList("WEB_APP"))` - causes compilation error  
✅ ALWAYS: `loggerBean.setChannelId("WEB_APP")` - correct String

**MANDATORY IMPORT FOR LOGGERBEAN USAGE:**
- **ALWAYS include**: `import java.util.Arrays;` when using LoggerBean with List setters
- **Required for Arrays.asList() type conversions**

**REFLECTION METHOD SIGNATURE VERIFICATION:**
- **BEFORE using getDeclaredMethod()**: Verify parameter types in source code
- **Example - String parameter**: `getDeclaredMethod("methodName", String.class, OtherClass.class)`
- **Example - List parameter**: `getDeclaredMethod("methodName", List.class, OtherClass.class)`
- **CRITICAL**: Method parameter types in reflection MUST match actual method signature

**SETTER METHOD TYPE CHECKING:**
- **String setters**: `setProperty("stringValue")`
- **List setters**: `setProperty(List.of("item1", "item2"))`
- **Boolean setters**: `setProperty(true)` or `setProperty(false)`
- **Integer setters**: `setProperty(123)`
- **ALWAYS verify setter parameter type before calling**

**MOCK METHOD PARAMETER TYPE MATCHING:**
- **when(mock.method(String param))**: Use `any(String.class)` or specific string
- **when(mock.method(List param))**: Use `any(List.class)` or `anyList()`
- **when(mock.method(Object param))**: Use `any()` or `any(Object.class)`
- **CRITICAL**: Mock parameter types must match actual method signature

🚨 **MANDATORY CONSTRUCTOR VERIFICATION PROCESS - READ THIS BEFORE CODING:**

**STEP 1: FIND EXACT CONSTRUCTOR IN SOURCE CODE BELOW**
- Look in the "Original Java Code" section below
- Search for `public ClassName(` to find constructor signatures  
- COUNT the exact number of parameters
- IDENTIFY each parameter type (int, String, Object, etc.)

**STEP 2: DYNAMIC CONSTRUCTOR ANALYSIS (WORKS FOR ANY JAVA CLASS)**
- Read the actual constructor signature from the source code
- Do NOT assume parameter patterns - always verify from source
- Constructor signatures vary by project and design
- Some classes may need 2, 3, 4, or more parameters
- Some classes may have multiple constructor overloads
- Parameter types can be primitives, objects, collections, etc.

**STEP 3: MANDATORY PRE-CODING CHECKLIST**
Before writing ANY constructor call, verify:
□ I found the exact constructor signature in the source code below
□ I counted the parameters correctly  
□ I will use the exact number of parameters required
□ I will provide appropriate values for each parameter type:
  - int/Integer: Use 400, 404, 500, 503, 0, 1, etc.
  - String: Use "Test message", "ERROR_CODE", etc.
  - boolean: Use true or false
  - Object types: Use `null` or mock objects
  - Collections: Use empty collections or null
  - Custom objects: Use mock instances

**CRITICAL COMPILATION ERROR PREVENTION:**
❌ NEVER assume constructor patterns
❌ NEVER use constructor calls without verifying parameter count
❌ NEVER skip parameters that exist in the source code
❌ NEVER hardcode specific class examples in tests
❌ NEVER mix up String and List types
❌ NEVER use wrong parameter types in reflection calls

✅ ALWAYS read the actual constructor from source code
✅ ALWAYS count parameters before writing constructor calls
✅ ALWAYS match the exact parameter count and types
✅ ALWAYS create dynamic test examples based on actual source
✅ ALWAYS verify parameter types before method calls
✅ ALWAYS use correct types in reflection getDeclaredMethod calls

**DYNAMIC CONSTRUCTOR EXAMPLES:**
```java
// Step 1: Found in source: public CustomException(int code, String message)
// Step 2: Parameter count: 2, types: int, String
// Step 3: Test usage:
CustomException exception = new CustomException(500, "Test error");

// Step 1: Found in source: public DataProcessor(List<String> data, boolean validate, Object context)
// Step 2: Parameter count: 3, types: List<String>, boolean, Object
// Step 3: Test usage:
DataProcessor processor = new DataProcessor(Arrays.asList("test"), true, null);
```

Original Java Code:
```java
{java_content}
```

CRITICAL TESTING RULES:
1. Generate ONLY the Java test code - NO comments, explanations, or markdown
2. NO /** JavaDoc comments */
3. NO // inline comments  
4. Clean, professional test code only
5. **NEVER test private methods directly - they are not accessible**
6. **For private methods with complex logic, use reflection with @Test annotation**
7. **Focus primarily on public/protected methods**
8. **INCLUDE ALL REQUIRED IMPORTS - DO NOT SKIP ANY IMPORTS**
9. **CRITICAL: Always use complete constructor signatures with ALL required parameters**
10. **When creating objects in tests, analyze the class signatures and include all constructor parameters**
11. **NEVER call getter/setter methods that don't exist in the actual class**
12. **NEVER use hardcoded strings for configuration values - use realistic test data or mocks**
13. **ALWAYS verify method exists before calling it in assertions**
14. **For configuration classes, test object creation and basic properties only**
15. Use realistic data patterns based on provided files
16. Include actual schema validation where applicable
17. Test with real configuration values and properties

⚠️ **MANDATORY CONSTRUCTOR VALIDATION STEP:**
Before writing ANY test method that creates an object:
1. Scroll up to the "Original Java Code" section above
2. Find the constructor for the class you want to create
3. Count the parameters in the constructor
4. Note each parameter type (int, String, Object, etc.)
5. Use that exact parameter count and types in your test

**DO NOT PROCEED WITHOUT COMPLETING THIS VALIDATION!**

🔍 **CONSTRUCTOR VALIDATION CHECKLIST:**
For EVERY object creation in your test, you MUST:
□ Find the constructor in the original Java code above
□ Count the parameters (e.g., 3 parameters)  
□ List the parameter types (e.g., int, String, Object)
□ Create object with exact parameter count
□ Use appropriate values for each type

**DYNAMIC VALIDATION EXAMPLES (ADAPT TO YOUR SOURCE CODE):**
```java
// Found in source: public AnyClass(int param1, String param2, Object param3)
// Parameter count: 3
// Parameter types: int, String, Object
// Correct test usage:
AnyClass instance = new AnyClass(123, "test value", null);

// Found in source: public AnyException(String errorCode, String message)  
// Parameter count: 2
// Parameter types: String, String
// Correct test usage:
AnyException exception = new AnyException("ERROR_CODE", "Error message");
```

MANDATORY IMPORT EXAMPLES:
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Optional;
import java.util.Arrays;
import java.time.LocalDateTime;
import java.time.LocalDate;
// Add other imports as needed based on the class being tested
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.assertThat;
```

Generate a complete JUnit 5 test class with:
- Proper package declaration
- **COMPREHENSIVE imports including ALL required classes**
- @ExtendWith(MockitoExtension.class)
- @Mock and @InjectMocks annotations
- @BeforeEach setup method
- Multiple @Test methods for each PUBLIC/PROTECTED method
- For private methods: Use reflection to access and test only if they contain complex business logic
- Edge case testing
- Exception testing with assertThrows()
- Parameterized tests where appropriate
- Schema validation tests (if Swagger files provided)
- Real test data usage (if test data files provided)

REFLECTION EXAMPLE for private methods:
```java
@Test
void testPrivateMethodName() throws Exception {{
    Method privateMethod = {class_name}.class.getDeclaredMethod("privateMethodName", parameterTypes);
    privateMethod.setAccessible(true);
    Object result = privateMethod.invoke(objectUnderTest, parameters);
    assertThat(result).isEqualTo(expectedValue);
}}
```

OUTPUT FORMAT: Return ONLY the complete Java test class code.
"""

STANDARD_JUNIT_PROMPT = """
Generate a CLEAN JUnit 5 test class with NO COMMENTS based on detailed analysis:

📊 **Class Analysis:**
- Package: {package}
- Class: {class_name}
- Frameworks: {frameworks}
- Complexity Score: {complexity_score}
- Public/Protected Methods: {method_count}
- Private Methods: {private_method_count}
- Field Count: {field_count}

🎯 **Testing Strategy:**
- Approaches: {testing_approaches}
- Complexity Level: {complexity_level}
- Mocking Strategy: {mocking_strategy}

📋 **Public/Protected Methods to Test (Direct Access):**
{methods_list}

🔒 **Private Methods (Use Reflection Only if Complex Logic):**
{private_methods_list}

🔍 **Method-Specific Strategies:**
{method_strategies}

⚠️ **Edge Cases to Cover:**
{edge_cases}

🚨 **MANDATORY CONSTRUCTOR VERIFICATION PROCESS - READ THIS BEFORE CODING:**

**STEP 1: FIND EXACT CONSTRUCTOR IN SOURCE CODE BELOW**
- Look in the "Original Java Code" section below
- Search for `public ClassName(` to find constructor signatures  
- COUNT the exact number of parameters
- IDENTIFY each parameter type (int, String, Object, etc.)

**STEP 2: DYNAMIC CONSTRUCTOR ANALYSIS (WORKS FOR ANY JAVA CLASS)**
- Read the actual constructor signature from the source code
- Do NOT assume parameter patterns - always verify from source
- Constructor signatures vary by project and design
- Some classes may need 2, 3, 4, or more parameters
- Some classes may have multiple constructor overloads
- Parameter types can be primitives, objects, collections, etc.

**STEP 3: MANDATORY PRE-CODING CHECKLIST**
Before writing ANY constructor call, verify:
□ I found the exact constructor signature in the source code below
□ I counted the parameters correctly  
□ I will use the exact number of parameters required
□ I will provide appropriate values for each parameter type:
  - int/Integer: Use 400, 404, 500, 503, 0, 1, etc.
  - String: Use "Test message", "ERROR_CODE", etc.
  - boolean: Use true or false
  - Object types: Use `null` or mock objects
  - Collections: Use empty collections or null
  - Custom objects: Use mock instances

**CRITICAL COMPILATION ERROR PREVENTION:**
❌ NEVER assume constructor patterns
❌ NEVER use constructor calls without verifying parameter count
❌ NEVER skip parameters that exist in the source code
❌ NEVER hardcode specific class examples in tests

✅ ALWAYS read the actual constructor from source code
✅ ALWAYS count parameters before writing constructor calls
✅ ALWAYS match the exact parameter count and types
✅ ALWAYS create dynamic test examples based on actual source

Original Java Code:
```java
{java_content}
```

CRITICAL TESTING RULES:
1. Generate ONLY the Java test code - NO comments or explanations
2. NO /** JavaDoc comments */
3. NO // inline comments
4. Clean, professional test code only
5. **NEVER test private methods directly - they are not accessible**
6. **For private methods with complex logic, use reflection with @Test annotation**
7. **Focus primarily on public/protected methods**
8. **INCLUDE ALL REQUIRED IMPORTS - DO NOT SKIP ANY IMPORTS**
9. **CRITICAL: Always use complete constructor signatures with ALL required parameters**
10. **When creating objects in tests, analyze the class signatures and include all constructor parameters**
11. **NEVER call getter/setter methods that don't exist in the actual class**
12. **NEVER use hardcoded strings for configuration values - use realistic test data or mocks**
13. **ALWAYS verify method exists before calling it in assertions**
14. **For configuration classes, test object creation and basic properties only**

⚠️ **MANDATORY CONSTRUCTOR VALIDATION STEP:**
Before writing ANY test method that creates an object:
1. Scroll up to the "Original Java Code" section above
2. Find the constructor for the class you want to create
3. Count the parameters in the constructor
4. Note each parameter type (int, String, Object, etc.)
5. Use that exact parameter count and types in your test

**DO NOT PROCEED WITHOUT COMPLETING THIS VALIDATION!**

🔍 **CONSTRUCTOR VALIDATION CHECKLIST:**
For EVERY object creation in your test, you MUST:
□ Find the constructor in the original Java code above
□ Count the parameters (e.g., 3 parameters)  
□ List the parameter types (e.g., int, String, Object)
□ Create object with exact parameter count
□ Use appropriate values for each type

**DYNAMIC VALIDATION EXAMPLES (ADAPT TO YOUR SOURCE CODE):**
```java
// Found in source: public AnyClass(int param1, String param2, Object param3)
// Parameter count: 3
// Parameter types: int, String, Object
// Correct test usage:
AnyClass instance = new AnyClass(123, "test value", null);

// Found in source: public AnyException(String errorCode, String message)  
// Parameter count: 2
// Parameter types: String, String
// Correct test usage:
AnyException exception = new AnyException("ERROR_CODE", "Error message");
```

CONSTRUCTOR PARAMETER REQUIREMENTS:
- Always examine the actual constructor signature from the imports and class analysis
- For any custom classes (exceptions, services, etc.), use ALL required parameters
- Use mock objects for complex parameters: @Mock HttpHeaders headers, @Mock Object context
- Example CORRECT object creation: new CustomClass(param1, param2, param3) - matching source signature
- Example INCORRECT object creation: new CustomClass(param1) - MISSING PARAMETERS!
- When testing methods that create objects, ensure the object creation uses complete signatures

DYNAMIC TESTING EXAMPLES:
```java
// CORRECT - Complete constructor with all parameters from source code
@Mock private Object mockDependency;
@Mock private String mockConfig;

@Test
void testMethodCreatesCustomObject() {
    // Read source: public CustomClass(String config, Object dependency, int value)
    // Use ALL constructor parameters
    CustomClass instance = new CustomClass("test-config", mockDependency, 100);
    
    assertThat(instance).isNotNull();
}

// WRONG - Missing required parameters based on source
@Test
void testWrongObjectCreation() {
    // DON'T DO THIS - missing parameters from source signature
    CustomClass instance = new CustomClass("config"); // COMPILATION ERROR!
}
```

MANDATORY IMPORT EXAMPLES:
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Optional;
import java.util.Arrays;
import java.time.LocalDateTime;
import java.time.LocalDate;
// Add other imports as needed based on the class being tested
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.assertThat;
```

Generate a complete, production-ready JUnit 5 test class with:
1. Proper package declaration matching the source
2. **COMPREHENSIVE imports including ALL required classes**
3. Class-level annotations (@ExtendWith(MockitoExtension.class) if using mocks)
4. Test setup and teardown methods (@BeforeEach, @AfterEach)
5. Mock declarations (@Mock, @InjectMocks) for dependencies
6. One test method per PUBLIC/PROTECTED method with multiple scenarios
7. For private methods: Use reflection to access and test only if they contain complex business logic
8. Edge case tests (null, empty, boundary values)
9. Exception testing with assertThrows()
10. Parameterized tests (@ParameterizedTest) where appropriate

REFLECTION EXAMPLE for private methods:
```java
@Test
void testPrivateMethodName() throws Exception {{
    Method privateMethod = {class_name}.class.getDeclaredMethod("privateMethodName", parameterTypes);
    privateMethod.setAccessible(true);
    Object result = privateMethod.invoke(objectUnderTest, parameters);
    assertThat(result).isEqualTo(expectedValue);
}}
```

Framework-Specific Patterns:
{framework_patterns}

OUTPUT FORMAT: Return ONLY the complete Java test class code.
"""
