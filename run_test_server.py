#!/usr/bin/env python3
"""Test server for DGI Toolkit API with isolated test environment."""

import os
import tempfile

import uvicorn

# Set up test environment
os.environ["DGI_ENVIRONMENT"] = "test"


# Create temporary test data
def create_test_data() -> str:
    """Create temporary test data file."""
    test_csv_content = """symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield
TEST1,Test Company 1,Technology,Software,0.025,30.0,0.08,5.0
TEST2,Test Company 2,Healthcare,Pharmaceuticals,0.035,45.0,0.12,4.5
TEST3,Test Company 3,Consumer,Retail,0.020,25.0,0.06,3.8
TEST4,Test Company 4,Finance,Banking,0.040,60.0,0.15,6.2
TEST5,Test Company 5,Energy,Oil & Gas,0.050,70.0,0.10,7.1"""

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    temp_file.write(test_csv_content)
    temp_file.close()

    return temp_file.name


if __name__ == "__main__":
    # Create test data and set environment
    test_data_path = create_test_data()
    os.environ["DGI_DATA_PATH"] = test_data_path

    print("🚀 Starting DGI Toolkit Test Server")
    print(f"📊 Using test data: {test_data_path}")
    print(f"🌍 Environment: {os.environ.get('DGI_ENVIRONMENT', 'unknown')}")
    print("🔗 API Documentation: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/healthz")
    print(
        "📈 Test Endpoint: http://localhost:8000/api/v1/screen?min_yield=0.02&top_n=3"
    )
    print("⚠️  This is a TEST server with isolated data!")

    try:
        uvicorn.run(
            "api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )
    finally:
        # Clean up test data file
        try:
            os.unlink(test_data_path)
            print(f"🧹 Cleaned up test data: {test_data_path}")
        except OSError:
            pass
