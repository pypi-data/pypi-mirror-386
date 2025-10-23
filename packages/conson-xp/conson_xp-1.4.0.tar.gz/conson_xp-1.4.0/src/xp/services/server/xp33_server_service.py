"""XP33 Server Service for device emulation.

This service provides XP33-specific device emulation functionality,
including response generation and device configuration handling for
3-channel light dimmer modules.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.server.base_server_service import BaseServerService


class XP33ServerError(Exception):
    """Raised when XP33 server operations fail."""

    pass


class XP33ServerService(BaseServerService):
    """
    XP33 device emulation service.

    Generates XP33-specific responses, handles XP33 device configuration,
    and implements XP33 telegram format for 3-channel dimmer modules.
    """

    def __init__(self, serial_number: str, variant: str = "XP33LR"):
        """Initialize XP33 server service.

        Args:
            serial_number: The device serial number.
            variant: Device variant (XP33, XP33LR, or XP33LED).
        """
        super().__init__(serial_number)
        self.variant = variant  # XP33 or XP33LR or XP33LED
        self.device_type = "XP33"
        self.module_type_code = ModuleTypeCode.XP33  # XP33 module type

        # XP33 device characteristics (anonymized for interoperability testing)
        if variant == "XP33LED":
            self.firmware_version = "XP33LED_V0.00.00"
            self.ean_code = "1234567890123"  # Test EAN - not a real product code
            self.max_power = 300  # 3 x 100VA
            self.module_type_code = ModuleTypeCode.XP33LED  # XP33LR module type
        elif variant == "XP33LR":  # XP33LR
            self.firmware_version = "XP33LR_V0.00.00"
            self.ean_code = "1234567890124"  # Test EAN - not a real product code
            self.max_power = 640  # Total 640VA
            self.module_type_code = ModuleTypeCode.XP33LR  # XP33LR module type
        else:  # XP33
            self.firmware_version = "XP33_V0.04.02"
            self.ean_code = "1234567890125"  # Test EAN - not a real product code
            self.max_power = 100  # Total 640VA
            self.module_type_code = ModuleTypeCode.XP33  # XP33 module type

        self.device_status = "00"  # Normal status
        self.link_number = 4  # 4 links configured
        self.autoreport_status = True

        # Channel states (3 channels, 0-100% dimming)
        self.channel_states = [0, 0, 0]  # All channels at 0%

        # Scene configuration (4 scenes)
        self.scenes = {
            1: [50, 30, 20],  # Scene 1: 50%, 30%, 20%
            2: [100, 100, 100],  # Scene 2: All full
            3: [25, 25, 25],  # Scene 3: Low level
            4: [0, 0, 0],  # Scene 4: Off
        }

    def _handle_device_specific_action_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP33-specific action requests."""
        telegrams = self._handle_action_channel_dimming(request.data)
        self.logger.debug(f"Generated {self.device_type} action responses: {telegrams}")
        return telegrams

    def _handle_action_channel_dimming(self, data_value: str) -> str:
        """Handle XP33-specific channel dimming action.

        Args:
            data_value: Action data in format channel_number:dimming_level.
                       E.g., "00:050" means channel 0, 50% dimming.

        Returns:
            Response telegram(s) - ACK/NAK, optionally with event telegram.
        """
        if ":" not in data_value or len(data_value) < 6:
            return self._build_ack_nak_response_telegram(False)

        try:
            parts = data_value.split(":")
            channel_number = int(parts[0])
            dimming_level = int(parts[1])
        except (ValueError, IndexError):
            return self._build_ack_nak_response_telegram(False)

        if channel_number not in range(len(self.channel_states)):
            return self._build_ack_nak_response_telegram(False)

        if dimming_level not in range(0, 101):
            return self._build_ack_nak_response_telegram(False)

        previous_level = self.channel_states[channel_number]
        self.channel_states[channel_number] = dimming_level
        state_changed = (previous_level == 0 and dimming_level > 0) or (
            previous_level > 0 and dimming_level == 0
        )

        telegrams = self._build_ack_nak_response_telegram(True)
        if state_changed and self.autoreport_status:
            # Report dimming change event
            telegrams += self._build_dimming_event_telegram(
                dimming_level, channel_number
            )

        return telegrams

    def _build_ack_nak_response_telegram(self, ack_or_nak: bool) -> str:
        """Build a complete ACK or NAK response telegram with checksum.

        Args:
            ack_or_nak: true: ACK telegram response, false: NAK telegram response.

        Returns:
            The complete telegram with checksum enclosed in angle brackets.
        """
        data_value = (
            SystemFunction.ACK.value if ack_or_nak else SystemFunction.NAK.value
        )
        data_part = f"R{self.serial_number}" f"F{data_value:02}D"
        return self._build_response_telegram(data_part)

    def _build_dimming_event_telegram(
        self, dimming_level: int, channel_number: int
    ) -> str:
        """Build a complete dimming event telegram with checksum.

        Args:
            dimming_level: Dimming level 0-100%.
            channel_number: Channel concerned (0-2).

        Returns:
            The complete event telegram with checksum enclosed in angle brackets.
        """
        data_value = "M" if dimming_level > 0 else "B"
        data_part = (
            f"E{self.module_type_code.value:02}"
            f"L{self.link_number:02}"
            f"I{channel_number:02}"
            f"{data_value}"
        )
        return self._build_response_telegram(data_part)

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP33-specific data requests."""
        if not request.datapoint_type:
            return None

        datapoint_type = request.datapoint_type
        handler = {
            DataPointType.MODULE_OUTPUT_STATE: self._handle_read_module_output_state,
            DataPointType.MODULE_STATE: self._handle_read_module_state,
            DataPointType.MODULE_OPERATING_HOURS: self._handle_read_module_operating_hours,
            DataPointType.MODULE_LIGHT_LEVEL: self._handle_read_light_level,
        }.get(datapoint_type)
        if not handler:
            return None

        data_value = handler()
        data_part = (
            f"R{self.serial_number}"
            f"F02D{datapoint_type.value}"
            f"{self.module_type_code.value:02}"
            f"{data_value}"
        )
        telegram = self._build_response_telegram(data_part)

        self.logger.debug(
            f"Generated {self.device_type} module type response: {telegram}"
        )
        return telegram

    def _handle_read_module_output_state(self) -> str:
        """Handle XP33-specific module output state.

        Returns:
            String representation of the output state for 3 channels.
        """
        return (
            f"xxxxx"
            f"{1 if self.channel_states[0] > 0 else 0}"
            f"{1 if self.channel_states[1] > 0 else 0}"
            f"{1 if self.channel_states[2] > 0 else 0}"
        )

    def _handle_read_module_state(self) -> str:
        """Handle XP33-specific module state.

        Returns:
            'ON' if any channel is active, 'OFF' otherwise.
        """
        if any(level > 0 for level in self.channel_states):
            return "ON"
        return "OFF"

    def _handle_read_module_operating_hours(self) -> str:
        """Handle XP33-specific module operating hours.

        Returns:
            Operating hours for all 3 channels.
        """
        return "00:000[H],01:000[H],02:000[H]"

    def _handle_read_light_level(self) -> str:
        """Handle XP33-specific light level reading.

        Returns:
            Light levels for all channels in format "00:000[%],01:000[%],02:000[%]".
        """
        levels = [
            f"{i:02d}:{level:03d}[%]" for i, level in enumerate(self.channel_states)
        ]
        return ",".join(levels)

    def set_channel_dimming(self, channel: int, level: int) -> bool:
        """Set individual channel dimming level.

        Args:
            channel: Channel number (1-3).
            level: Dimming level (0-100 percent).

        Returns:
            True if channel was set successfully, False otherwise.
        """
        if 1 <= channel <= 3 and 0 <= level <= 100:
            self.channel_states[channel - 1] = level
            self.logger.info(f"XP33 channel {channel} set to {level}%")
            return True
        return False

    def activate_scene(self, scene: int) -> bool:
        """Activate a pre-programmed scene.

        Args:
            scene: Scene number (1-4).

        Returns:
            True if scene was activated successfully, False otherwise.
        """
        if scene in self.scenes:
            self.channel_states = self.scenes[scene].copy()
            self.logger.info(f"XP33 scene {scene} activated: {self.channel_states}")
            return True
        return False

    def get_device_info(self) -> Dict:
        """Get XP33 device information.

        Returns:
            Dictionary containing device information.
        """
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "variant": self.variant,
            "firmware_version": self.firmware_version,
            "ean_code": self.ean_code,
            "max_power": self.max_power,
            "status": self.device_status,
            "link_number": self.link_number,
            "autoreport_status": self.autoreport_status,
            "channel_states": self.channel_states.copy(),
            "available_scenes": list(self.scenes.keys()),
        }

    def get_technical_specs(self) -> Dict:
        """Get technical specifications.

        Returns:
            Dictionary containing technical specifications.
        """
        if self.variant == "XP33LED":
            return {
                "power_per_channel": "100VA",
                "total_power": "300VA",
                "load_types": ["LED lamps", "resistive", "capacitive"],
                "dimming_type": "Leading/Trailing edge configurable",
                "protection": "Short-circuit proof channels",
            }

        # XP33LR
        return {
            "power_per_channel": "500VA max",
            "total_power": "640VA",
            "load_types": ["Resistive", "inductive"],
            "dimming_type": "Leading edge, logarithmic control",
            "protection": "Thermal protection, neutral break detection",
        }
