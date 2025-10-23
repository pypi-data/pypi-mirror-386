"""
PyUVM Register Abstraction Layer Model

Auto-generated from SystemRDL specification using excel2pyral converter

Package: PROJECT_TEST_ral
Generated: 2025-10-22 05:44:39

This file contains Python-based PyUVM RAL classes that follow proper UVM structure
for use in Python verification environments using the PyUVM framework.

Usage:
    from PROJECT_TEST_ral import build_ral_model
    
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

class ProjectTestTestCtrlAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CTRL_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CTRL_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CTRL_ADDR = uvm_reg_field.type_id.create("TEST_CTRL_ADDR")
        self.TEST_CTRL_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Control Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestStsAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_STS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_STS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_STS_ADDR = uvm_reg_field.type_id.create("TEST_STS_ADDR")
        self.TEST_STS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Status Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestRuptcntAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_RUPTCNT_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_RUPTCNT_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_RUPTCNT_ADDR = uvm_reg_field.type_id.create("TEST_RUPTCNT_ADDR")
        self.TEST_RUPTCNT_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Packet interrupt count address
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0EnAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_EN_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_EN_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_EN_ADDR = uvm_reg_field.type_id.create("TEST_CH0_EN_ADDR")
        self.TEST_CH0_EN_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Bit 0, TEST Channel 0 Enable.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0DdrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_DDR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_DDR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_DDR_ADDR = uvm_reg_field.type_id.create("TEST_CH0_DDR_ADDR")
        self.TEST_CH0_DDR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 PSDDR4 Address.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0PktAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_PKT_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_PKT_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_PKT_ADDR = uvm_reg_field.type_id.create("TEST_CH0_PKT_ADDR")
        self.TEST_CH0_PKT_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 Packet Size.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0BufAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_BUF_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_BUF_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_BUF_ADDR = uvm_reg_field.type_id.create("TEST_CH0_BUF_ADDR")
        self.TEST_CH0_BUF_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 Data Buffer Size.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0StsAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_STS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_STS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_STS_ADDR = uvm_reg_field.type_id.create("TEST_CH0_STS_ADDR")
        self.TEST_CH0_STS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 Status Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0WrpAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_WRP_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_WRP_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_WRP_ADDR = uvm_reg_field.type_id.create("TEST_CH0_WRP_ADDR")
        self.TEST_CH0_WRP_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 Write Pointer Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0MfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_MFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_MFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_MFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH0_MFIFO_ADDR")
        self.TEST_CH0_MFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 Monitor FIFO Output Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0IfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_IFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_IFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_IFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH0_IFIFO_ADDR")
        self.TEST_CH0_IFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # PulseMetrics FIFO Status Flags Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1EnAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_EN_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_EN_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_EN_ADDR = uvm_reg_field.type_id.create("TEST_CH1_EN_ADDR")
        self.TEST_CH1_EN_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Bit 0, TEST Channel 1 Enable.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1DdrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_DDR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_DDR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_DDR_ADDR = uvm_reg_field.type_id.create("TEST_CH1_DDR_ADDR")
        self.TEST_CH1_DDR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 PSDDR4 Address.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1PktAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_PKT_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_PKT_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_PKT_ADDR = uvm_reg_field.type_id.create("TEST_CH1_PKT_ADDR")
        self.TEST_CH1_PKT_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 Packet Size in 64 bit words.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1BufAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_BUF_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_BUF_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_BUF_ADDR = uvm_reg_field.type_id.create("TEST_CH1_BUF_ADDR")
        self.TEST_CH1_BUF_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 Data Buffer Size.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1StsAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_STS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_STS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_STS_ADDR = uvm_reg_field.type_id.create("TEST_CH1_STS_ADDR")
        self.TEST_CH1_STS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 Status Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1WrpAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_WRP_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_WRP_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_WRP_ADDR = uvm_reg_field.type_id.create("TEST_CH1_WRP_ADDR")
        self.TEST_CH1_WRP_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 Write Pointer Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1MfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_MFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_MFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_MFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH1_MFIFO_ADDR")
        self.TEST_CH1_MFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 Monitor FIFO Output Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1IfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_IFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_IFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_IFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH1_IFIFO_ADDR")
        self.TEST_CH1_IFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # ATEST CHA FIFO Status Flags Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2EnAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_EN_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_EN_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_EN_ADDR = uvm_reg_field.type_id.create("TEST_CH2_EN_ADDR")
        self.TEST_CH2_EN_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Bit 0, TEST Channel 2 Enable.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2DdrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_DDR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_DDR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_DDR_ADDR = uvm_reg_field.type_id.create("TEST_CH2_DDR_ADDR")
        self.TEST_CH2_DDR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 PSDDR4 Address.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2PktAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_PKT_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_PKT_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_PKT_ADDR = uvm_reg_field.type_id.create("TEST_CH2_PKT_ADDR")
        self.TEST_CH2_PKT_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 Packet Size in 64 bit words.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2BufAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_BUF_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_BUF_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_BUF_ADDR = uvm_reg_field.type_id.create("TEST_CH2_BUF_ADDR")
        self.TEST_CH2_BUF_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 Data Buffer Size.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2StsAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_STS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_STS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_STS_ADDR = uvm_reg_field.type_id.create("TEST_CH2_STS_ADDR")
        self.TEST_CH2_STS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 Status Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2WrpAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_WRP_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_WRP_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_WRP_ADDR = uvm_reg_field.type_id.create("TEST_CH2_WRP_ADDR")
        self.TEST_CH2_WRP_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 Write Pointer Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2MfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_MFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_MFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_MFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH2_MFIFO_ADDR")
        self.TEST_CH2_MFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 Monitor FIFO Output Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2IfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_IFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_IFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_IFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH2_IFIFO_ADDR")
        self.TEST_CH2_IFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # ATEST CHB FIFO Status Flags Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3EnAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_EN_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_EN_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_EN_ADDR = uvm_reg_field.type_id.create("TEST_CH3_EN_ADDR")
        self.TEST_CH3_EN_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Bit 0, TEST Channel 3 Enable.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3DdrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_DDR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_DDR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_DDR_ADDR = uvm_reg_field.type_id.create("TEST_CH3_DDR_ADDR")
        self.TEST_CH3_DDR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 PSDDR4 Address.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3PktAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_PKT_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_PKT_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_PKT_ADDR = uvm_reg_field.type_id.create("TEST_CH3_PKT_ADDR")
        self.TEST_CH3_PKT_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 Packet Size in 64 bit words.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3BufAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_BUF_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_BUF_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_BUF_ADDR = uvm_reg_field.type_id.create("TEST_CH3_BUF_ADDR")
        self.TEST_CH3_BUF_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 Data Buffer Size.
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3StsAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_STS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_STS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_STS_ADDR = uvm_reg_field.type_id.create("TEST_CH3_STS_ADDR")
        self.TEST_CH3_STS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 Status Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3WrpAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_WRP_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_WRP_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_WRP_ADDR = uvm_reg_field.type_id.create("TEST_CH3_WRP_ADDR")
        self.TEST_CH3_WRP_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 Write Pointer Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3MfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_MFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_MFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_MFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH3_MFIFO_ADDR")
        self.TEST_CH3_MFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 Monitor FIFO Output Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3IfifoAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_IFIFO_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_IFIFO_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_IFIFO_ADDR = uvm_reg_field.type_id.create("TEST_CH3_IFIFO_ADDR")
        self.TEST_CH3_IFIFO_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Debug Channel 3 FIFO Status Flags Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestInpFmtCtrl0Addr(uvm_reg):
    """Register: PROJECT_TEST::TEST_INP_FMT_CTRL0_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_INP_FMT_CTRL0_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_INP_FMT_CTRL0_ADDR = uvm_reg_field.type_id.create("TEST_INP_FMT_CTRL0_ADDR")
        self.TEST_INP_FMT_CTRL0_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Input Format Module Control Word0
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestInpFmtCtrl1Addr(uvm_reg):
    """Register: PROJECT_TEST::TEST_INP_FMT_CTRL1_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_INP_FMT_CTRL1_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_INP_FMT_CTRL1_ADDR = uvm_reg_field.type_id.create("TEST_INP_FMT_CTRL1_ADDR")
        self.TEST_INP_FMT_CTRL1_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Input Format Module Control Word1
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestLclpulseCtrlAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_LCLPULSE_CTRL_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_LCLPULSE_CTRL_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_LCLPULSE_CTRL_ADDR = uvm_reg_field.type_id.create("TEST_LCLPULSE_CTRL_ADDR")
        self.TEST_LCLPULSE_CTRL_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Local Pulse Waveform Generator Control Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestLclpulseRdataAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_LCLPULSE_RDATA_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_LCLPULSE_RDATA_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_LCLPULSE_RDATA_ADDR = uvm_reg_field.type_id.create("TEST_LCLPULSE_RDATA_ADDR")
        self.TEST_LCLPULSE_RDATA_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Waveform Buffer Read Data
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestAdvci2DataReplayCtrlAddr(uvm_reg):
    """Register: PROJECT_TEST::ADVCI2_DATA_REPLAY_CTRL_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::ADVCI2_DATA_REPLAY_CTRL_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.ADVCI2_DATA_REPLAY_CTRL_ADDR = uvm_reg_field.type_id.create("ADVCI2_DATA_REPLAY_CTRL_ADDR")
        self.ADVCI2_DATA_REPLAY_CTRL_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Data Replay Module Control Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestAdvci2DataReplayStsAddr(uvm_reg):
    """Register: PROJECT_TEST::ADVCI2_DATA_REPLAY_STS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::ADVCI2_DATA_REPLAY_STS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.ADVCI2_DATA_REPLAY_STS_ADDR = uvm_reg_field.type_id.create("ADVCI2_DATA_REPLAY_STS_ADDR")
        self.ADVCI2_DATA_REPLAY_STS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Bit 0, Data Replay Module FIFO Data Lost
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestAdvci2DataReplayTxfrLengthAddr(uvm_reg):
    """Register: PROJECT_TEST::ADVCI2_DATA_REPLAY_TXFR_LENGTH_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::ADVCI2_DATA_REPLAY_TXFR_LENGTH_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.ADVCI2_DATA_REPLAY_TXFR_LENGTH_ADDR = uvm_reg_field.type_id.create("ADVCI2_DATA_REPLAY_TXFR_LENGTH_ADDR")
        self.ADVCI2_DATA_REPLAY_TXFR_LENGTH_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Number of 32 Bit Words Transferred from DDR into FPGA Via AXI DMA
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestLclpulseBufrLengthAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_LCLPULSE_BUFR_LENGTH_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_LCLPULSE_BUFR_LENGTH_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_LCLPULSE_BUFR_LENGTH_ADDR = uvm_reg_field.type_id.create("TEST_LCLPULSE_BUFR_LENGTH_ADDR")
        self.TEST_LCLPULSE_BUFR_LENGTH_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Local Pulse Waveform Buffer Length Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestLclpulseWdataAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_LCLPULSE_WDATA_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_LCLPULSE_WDATA_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_LCLPULSE_WDATA_ADDR = uvm_reg_field.type_id.create("TEST_LCLPULSE_WDATA_ADDR")
        self.TEST_LCLPULSE_WDATA_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Waveform Buffer Write Data
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestLclpulseCexPosCntsAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_LCLPULSE_CEX_POS_CNTS_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_LCLPULSE_CEX_POS_CNTS_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_LCLPULSE_CEX_POS_CNTS_ADDR = uvm_reg_field.type_id.create("TEST_LCLPULSE_CEX_POS_CNTS_ADDR")
        self.TEST_LCLPULSE_CEX_POS_CNTS_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Local CEX Rising and Falling Edges Position Counts Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh0RuptcntrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH0_RUPTCNTR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH0_RUPTCNTR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH0_RUPTCNTR_ADDR = uvm_reg_field.type_id.create("TEST_CH0_RUPTCNTR_ADDR")
        self.TEST_CH0_RUPTCNTR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 0 Packet Interrupt Counter Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh1RuptcntrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH1_RUPTCNTR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH1_RUPTCNTR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH1_RUPTCNTR_ADDR = uvm_reg_field.type_id.create("TEST_CH1_RUPTCNTR_ADDR")
        self.TEST_CH1_RUPTCNTR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 1 Packet Interrupt Counter Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh2RuptcntrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH2_RUPTCNTR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH2_RUPTCNTR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH2_RUPTCNTR_ADDR = uvm_reg_field.type_id.create("TEST_CH2_RUPTCNTR_ADDR")
        self.TEST_CH2_RUPTCNTR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 2 Packet Interrupt Counter Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestCh3RuptcntrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_CH3_RUPTCNTR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_CH3_RUPTCNTR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_CH3_RUPTCNTR_ADDR = uvm_reg_field.type_id.create("TEST_CH3_RUPTCNTR_ADDR")
        self.TEST_CH3_RUPTCNTR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # Channel 3 Packet Interrupt Counter Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestInterruptMaskAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_INTERRUPT_MASK_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_INTERRUPT_MASK_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_INTERRUPT_MASK_ADDR = uvm_reg_field.type_id.create("TEST_INTERRUPT_MASK_ADDR")
        self.TEST_INTERRUPT_MASK_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Interrupt Mask Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestInterruptClrAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_INTERRUPT_CLR_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_INTERRUPT_CLR_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_INTERRUPT_CLR_ADDR = uvm_reg_field.type_id.create("TEST_INTERRUPT_CLR_ADDR")
        self.TEST_INTERRUPT_CLR_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Interrupt Clear Register, Auto Reset
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestInterruptStateAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_INTERRUPT_STATE_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_INTERRUPT_STATE_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_INTERRUPT_STATE_ADDR = uvm_reg_field.type_id.create("TEST_INTERRUPT_STATE_ADDR")
        self.TEST_INTERRUPT_STATE_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RO",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Interrupt Status Register
        
    def build(self):
        """Build phase - configure register"""
        super().build()
        # Additional register-specific configuration can be added here
        pass

class ProjectTestTestDumpAddr(uvm_reg):
    """Register: PROJECT_TEST::TEST_DUMP_ADDR"""
    
    def __init__(self, name="PROJECT_TEST::TEST_DUMP_ADDR"):
        super().__init__(name, 32, has_coverage=uvm_cvr_t.UVM_CVR_ALL)
        
        # Create fields
        self.TEST_DUMP_ADDR = uvm_reg_field.type_id.create("TEST_DUMP_ADDR")
        self.TEST_DUMP_ADDR.configure(
            parent=self,
            size=32,
            lsb=0,
            access="RW",
            has_reset=True,
            reset_value=0x0,
            has_coverage=uvm_cvr_t.UVM_CVR_ALL
        )
        # TEST Scratch Register
        
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

class ProjectTest(uvm_reg_block):
    """Top-level register block: PROJECT_TEST"""
    
    def __init__(self, name="PROJECT_TEST"):
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
        ProjectTest: The top-level register block instance
    """
    ral = ProjectTest.type_id.create("PROJECT_TEST")
    
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
