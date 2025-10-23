"""
PyUVM Register Abstraction Layer Model

Auto-generated from SystemRDL specification using excel2pyral converter

Package: mychip_ral
Generated: 2025-10-22 05:33:28

This file contains Python-based PyUVM RAL classes that follow proper UVM structure
for use in Python verification environments using the PyUVM framework.

Usage:
    from mychip_ral import build_ral_model
    
    ral = build_ral_model()
    # Use ral in your PyUVM testbench
"""

from pyuvm import *
from typing import Optional, Dict, Any, List
import asyncio

# Enhanced UVM classes (if available)
try:
    from uvm_reg_enhanced import uvm_reg
    from uvm_reg_map_enhanced import uvm_reg_map  
    from uvm_reg_coverage import enable_register_coverage, enable_block_coverage
    from uvm_mem import uvm_mem
    ENHANCED_CLASSES_AVAILABLE = True
except ImportError:
    # Fall back to standard PyUVM classes
    ENHANCED_CLASSES_AVAILABLE = False
    print("Warning: Enhanced UVM classes not available, using standard PyUVM")

# ============================================================================
# Register Classes (Type-Based)
# ============================================================================

class MychipCrtlReg(uvm_reg):
    """Register: mychip::CRTL_REG"""
    
    def __init__(self, name="mychip::CRTL_REG"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.ENABLE = uvm_reg_field.type_id.create("ENABLE")
        self.ENABLE.configure(
            parent=self,
            size=1,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Enable GPIO
        
        self.MODE = uvm_reg_field.type_id.create("MODE")
        self.MODE.configure(
            parent=self,
            size=3,
            lsb=1,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Mode Select
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class MychipStatusReg(uvm_reg):
    """Register: mychip::STATUS_REG"""
    
    def __init__(self, name="mychip::STATUS_REG"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.READY = uvm_reg_field.type_id.create("READY")
        self.READY.configure(
            parent=self,
            size=1,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Ready flag
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class MychipResetReg(uvm_reg):
    """Register: mychip::RESET_REG"""
    
    def __init__(self, name="mychip::RESET_REG"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.PAUSE = uvm_reg_field.type_id.create("PAUSE")
        self.PAUSE.configure(
            parent=self,
            size=1,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Pause txn UART
        
        self.START = uvm_reg_field.type_id.create("START")
        self.START.configure(
            parent=self,
            size=3,
            lsb=1,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Start Txn UART
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class MychipStopReg(uvm_reg):
    """Register: mychip::STOP_REG"""
    
    def __init__(self, name="mychip::STOP_REG"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.END = uvm_reg_field.type_id.create("END")
        self.END.configure(
            parent=self,
            size=1,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Stop Txn UART
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

# ============================================================================
# Register Block Classes (Type-Based)
# ============================================================================

# ============================================================================
# Top-Level RAL Class (Contains Sub-Block Instances)
# ============================================================================

class Mychip(uvm_reg_block):
    """Top-level register block: mychip"""
    
    def __init__(self, name="mychip"):
        super().__init__(name, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create sub-block instances (like SystemVerilog UVM structure)

    def build_phase(self, phase):
        """Build phase - create register map and configure sub-blocks"""
        super().build_phase(phase)
        
        # Create default map
        self.default_map = uvm_reg_map.type_id.create("default_map") if ENHANCED_CLASSES_AVAILABLE else create_reg_map("default_map")
        self.default_map.configure(self, 0x0)
        
        # Configure and add sub-blocks to map (equivalent to add_submap)
        
        # Lock the model
        self.lock_model()
        
    def get_all_registers(self) -> List[uvm_reg]:
        """Get all registers from all sub-blocks"""
        all_registers = []
        return all_registers

# ============================================================================
# RAL Model Builder Functions
# ============================================================================

def build_ral_model():
    """
    Build and return the top-level RAL model
    
    Returns:
        Mychip: The top-level register block instance
    """
    ral = Mychip.type_id.create("mychip")
    
    # Build the model
    phase = uvm_build_phase("build")
    ral.build_phase(phase)
    
    # Enable coverage if enhanced classes are available
    if ENHANCED_CLASSES_AVAILABLE:
        try:
            enable_block_coverage(ral)
        except:
            pass  # Coverage enhancement not available
    
    return ral

def get_ral_model():
    """Legacy function name for compatibility"""
    return build_ral_model()

def create_reg_map(name: str):
    """Helper function to create register map when enhanced classes not available"""
    # Fallback implementation
    class BasicRegMap:
        def __init__(self, name):
            self.name = name
            self._registers = []
            self._submaps = []
            
        def configure(self, parent, base_addr):
            self.parent = parent
            self.base_addr = base_addr
            
        def add_reg(self, reg, addr, access):
            self._registers.append((reg, addr, access))
            
        def add_submap(self, submap, addr):
            """Add submap at specified address (like SystemVerilog add_submap)"""
            self._submaps.append((submap, addr))
            
        def add_mem(self, mem, addr, access):
            pass  # Basic implementation
            
    return BasicRegMap(name)

# ============================================================================
# Usage Example and Testing
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("Building RAL model...")
    model = build_ral_model()
    
    all_registers = model.get_all_registers()
    print(f"Generated RAL model with {len(all_registers)} total registers:")
    
    # Show hierarchy like SystemVerilog UVM
    print("\nRAL Hierarchy:")
    
    print("\nRAL model ready for use in PyUVM testbench!")
    
    # Example of how to use in a test (following UVM structure)
    print("\nExample usage in test:")
    print("  ral = build_ral_model()")
