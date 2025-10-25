# Post-Processing Module - Refactored Architecture

## Overview

This module provides a comprehensive, refactored post-processing system for the Matrice Python SDK. The system has been completely redesigned to be more pythonic, maintainable, and extensible while providing powerful analytics capabilities for various use cases.

## 🚀 Key Features

### ✅ **Unified Architecture**
- **Single Entry Point**: `PostProcessor` class handles all processing needs
- **Standardized Results**: All operations return `ProcessingResult` objects
- **Consistent Configuration**: Type-safe configuration system with validation
- **Registry Pattern**: Easy registration and discovery of use cases

### ✅ **Separate Use Case Classes**
- **People Counting**: Advanced people counting with zone analysis and tracking
- **Customer Service**: Comprehensive customer service analytics with business intelligence
- **Extensible Design**: Easy to add new use cases

### ✅ **Pythonic Configuration Management**
- **Dataclass-based**: Type-safe configurations using dataclasses
- **Nested Configurations**: Support for complex nested config structures
- **File Support**: JSON/YAML configuration file loading and saving
- **Validation**: Built-in validation with detailed error messages

### ✅ **Comprehensive Error Handling**
- **Standardized Errors**: All errors return structured `ProcessingResult` objects
- **Detailed Information**: Error messages include type, context, and debugging info
- **Graceful Degradation**: System continues operating even with partial failures

### ✅ **Processing Statistics**
- **Performance Tracking**: Automatic processing time measurement
- **Success Metrics**: Success/failure rates and statistics
- **Insights Generation**: Automatic generation of actionable insights

## 📁 Architecture

```
post_processing/
├── __init__.py              # Main exports and convenience functions
├── processor.py             # Main PostProcessor class
├── README.md               # This documentation
│
├── core/                   # Core system components
│   ├── __init__.py
│   ├── base.py            # Base classes, enums, and protocols
│   ├── config.py          # Configuration system
│   └── advanced_usecases.py # Advanced use case implementations
│
├── usecases/              # Separate use case implementations
│   ├── __init__.py
│   ├── people_counting.py # People counting use case
│   └── customer_service.py # Customer service use case
│
└── utils/                 # Utility functions organized by category
    ├── __init__.py
    ├── geometry_utils.py  # Geometric calculations
    ├── format_utils.py    # Format detection and conversion
    ├── filter_utils.py    # Filtering and cleaning operations
    ├── counting_utils.py  # Counting and aggregation
    └── tracking_utils.py  # Tracking and movement analysis
```

## 🛠 Quick Start

### Basic Usage

```python
from matrice_analytics.post_processing import PostProcessor, process_simple

# Method 1: Simple processing (recommended for quick tasks)
result = process_simple(
    raw_results,
    usecase="people_counting",
    confidence_threshold=0.5
)

# Method 2: Using PostProcessor class (recommended for complex workflows)
processor = PostProcessor()
result = processor.process_simple(
    raw_results,
    usecase="people_counting", 
    confidence_threshold=0.5,
    enable_tracking=True
)

print(f"Status: {result.status.value}")
print(f"Summary: {result.summary}")
print(f"Insights: {len(result.insights)} generated")
```

### Advanced Configuration

```python
# Create complex configuration
config = processor.create_config(
    'people_counting',
    confidence_threshold=0.6,
    enable_tracking=True,
    person_categories=['person', 'people', 'human'],
    zone_config={
        'zones': {
            'entrance': [[0, 0], [100, 0], [100, 100], [0, 100]],
            'checkout': [[200, 200], [300, 200], [300, 300], [200, 300]]
        }
    },
    alert_config={
        'count_thresholds': {'all': 10},
        'occupancy_thresholds': {'entrance': 5}
    }
)

# Process with configuration
result = processor.process(raw_results, config)
```

### Configuration File Support

```python
# Save configuration to file
processor.save_config(config, "people_counting_config.json")

# Load and use configuration from file
result = processor.process_from_file(raw_results, "people_counting_config.json")
```

## 📊 Use Cases

### 1. People Counting (`people_counting`)

Advanced people counting with comprehensive analytics:

```python
result = process_simple(
    raw_results,
    usecase="people_counting",
    confidence_threshold=0.5,
    enable_tracking=True,
    person_categories=['person', 'people'],
    zone_config={
        'zones': {
            'entrance': [[0, 0], [100, 0], [100, 100], [0, 100]]
        }
    }
)
```

**Features:**
- Multi-category person detection
- Zone-based counting and analysis
- Unique person tracking
- Occupancy analysis
- Alert generation based on thresholds
- Temporal analysis and trends

### 2. Customer Service (`customer_service`)

Comprehensive customer service analytics:

```python
result = process_simple(
    raw_results,
    usecase="customer_service",
    confidence_threshold=0.6,
    service_proximity_threshold=50.0,
    staff_categories=['staff', 'employee'],
    customer_categories=['customer', 'person']
)
```

**Features:**
- Staff utilization analysis
- Customer-staff interaction detection
- Service quality metrics
- Area occupancy analysis
- Queue management insights
- Business intelligence metrics

## 🔧 Configuration System

### Configuration Classes

All configurations are type-safe dataclasses with built-in validation:

```python
from matrice_analytics.post_processing import PeopleCountingConfig, ZoneConfig

# Create configuration programmatically
config = PeopleCountingConfig(
    confidence_threshold=0.5,
    enable_tracking=True,
    zone_config=ZoneConfig(
        zones={
            'entrance': [[0, 0], [100, 0], [100, 100], [0, 100]]
        }
    )
)

# Validate configuration
errors = config.validate()
if errors:
    print(f"Configuration errors: {errors}")
```

### Configuration Templates

```python
# Get configuration template for a use case
template = processor.get_config_template('people_counting')
print(f"Available options: {list(template.keys())}")

# List all available use cases
use_cases = processor.list_available_usecases()
print(f"Available use cases: {use_cases}")
```

## 📈 Processing Results

All processing operations return a standardized `ProcessingResult` object:

```python
class ProcessingResult:
    data: Any                           # Processed data
    status: ProcessingStatus           # SUCCESS, ERROR, WARNING, PARTIAL
    usecase: str                       # Use case name
    category: str                      # Use case category
    processing_time: float             # Processing time in seconds
    summary: str                       # Human-readable summary
    insights: List[str]                # Generated insights
    warnings: List[str]                # Warning messages
    error_message: Optional[str]       # Error message if failed
    predictions: List[Dict[str, Any]]  # Detailed predictions
    metrics: Dict[str, Any]            # Performance metrics
```

### Working with Results

```python
result = processor.process_simple(data, "people_counting")

# Check status
if result.is_success():
    print(f"✅ {result.summary}")
    
    # Access insights
    for insight in result.insights:
        print(f"💡 {insight}")
    
    # Access metrics
    print(f"📊 Metrics: {result.metrics}")
    
    # Access processed data
    processed_data = result.data
else:
    print(f"❌ Processing failed: {result.error_message}")
```

## 📊 Statistics and Monitoring

```python
# Get processing statistics
stats = processor.get_statistics()
print(f"Total processed: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average processing time: {stats['average_processing_time']:.3f}s")

# Reset statistics
processor.reset_statistics()
```

## 🔌 Extensibility

### Adding New Use Cases

1. **Create Use Case Class**:

```python
from matrice_analytics.post_processing.core.base import BaseProcessor

class MyCustomUseCase(BaseProcessor):
    def __init__(self):
        super().__init__("my_custom_usecase")
        self.category = "custom"
    
    def process(self, data, config, context=None):
        # Implement your processing logic
        return self.create_result(processed_data, "my_custom_usecase", "custom")
```

2. **Register Use Case**:

```python
from matrice_analytics.post_processing.core.base import registry

registry.register_use_case("custom", "my_custom_usecase", MyCustomUseCase)
```

### Adding New Utility Functions

Add utility functions to the appropriate module in the `utils/` directory and export them in `utils/__init__.py`.

## 🧪 Testing

The system includes comprehensive error handling and validation. Here's how to test your implementations:

```python
# Test configuration validation
errors = processor.validate_config({
    'usecase': 'people_counting',
    'confidence_threshold': 0.5
})

# Test with sample data
sample_data = [
    {'category': 'person', 'confidence': 0.8, 'bbox': [10, 10, 50, 50]}
]

result = process_simple(sample_data, 'people_counting')
assert result.is_success()
```

## 🔄 Migration from Old System

If you're migrating from the old post-processing system:

1. **Update Imports**:
   ```python
   # Old
   from matrice_analytics.old_post_processing import some_function
   
   # New
   from matrice_analytics.post_processing import PostProcessor, process_simple
   ```

2. **Update Processing Calls**:
   ```python
   # Old
   result = old_process_function(data, config_dict)
   
   # New
   result = process_simple(data, "usecase_name", **config_dict)
   ```

3. **Update Configuration**:
   ```python
   # Old
   config = {"threshold": 0.5, "enable_tracking": True}
   
   # New
   config = processor.create_config("people_counting", 
                                   confidence_threshold=0.5, 
                                   enable_tracking=True)
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Use Case Not Found**:
   ```python
   # Check available use cases
   print(processor.list_available_usecases())
   ```

2. **Configuration Validation Errors**:
   ```python
   # Validate configuration
   errors = processor.validate_config(config)
   if errors:
       print(f"Validation errors: {errors}")
   ```

3. **Processing Failures**:
   ```python
   # Check result status and error details
   if not result.is_success():
       print(f"Error: {result.error_message}")
       print(f"Error type: {result.error_type}")
       print(f"Error details: {result.error_details}")
   ```

## 📝 API Reference

### Main Classes

- **`PostProcessor`**: Main processing class
- **`ProcessingResult`**: Standardized result container
- **`BaseConfig`**: Base configuration class
- **`PeopleCountingConfig`**: People counting configuration
- **`CustomerServiceConfig`**: Customer service configuration

### Convenience Functions

- **`process_simple()`**: Simple processing function
- **`create_config_template()`**: Get configuration template
- **`list_available_usecases()`**: List available use cases
- **`validate_config()`**: Validate configuration

### Utility Functions

The system provides comprehensive utility functions organized by category:

- **Geometry**: Point-in-polygon, distance calculations, IoU
- **Format**: Format detection and conversion
- **Filter**: Confidence filtering, deduplication
- **Counting**: Object counting, zone analysis
- **Tracking**: Movement analysis, line crossing detection

## 🎯 Best Practices

1. **Use Simple Processing for Quick Tasks**:
   ```python
   result = process_simple(data, "people_counting", confidence_threshold=0.5)
   ```

2. **Use PostProcessor Class for Complex Workflows**:
   ```python
   processor = PostProcessor()
   config = processor.create_config("people_counting", **params)
   result = processor.process(data, config)
   ```

3. **Always Check Result Status**:
   ```python
   if result.is_success():
       # Process successful result
   else:
       # Handle error
   ```

4. **Use Configuration Files for Complex Setups**:
   ```python
   processor.save_config(config, "config.json")
   result = processor.process_from_file(data, "config.json")
   ```

5. **Monitor Processing Statistics**:
   ```python
   stats = processor.get_statistics()
   # Monitor success rates and performance
   ```

## 🔮 Future Enhancements

The refactored system is designed for easy extension. Planned enhancements include:

- Additional use cases (security monitoring, retail analytics)
- Advanced tracking algorithms
- Real-time processing capabilities
- Integration with external analytics platforms
- Machine learning-based insights generation

---

**The refactored post-processing system provides a solid foundation for scalable, maintainable, and powerful analytics capabilities. The clean architecture makes it easy to extend and customize for specific use cases while maintaining consistency and reliability.** 