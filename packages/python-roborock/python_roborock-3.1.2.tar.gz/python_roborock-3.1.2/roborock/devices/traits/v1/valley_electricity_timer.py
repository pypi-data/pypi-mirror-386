from roborock.data import ValleyElectricityTimer
from roborock.devices.traits.v1 import common
from roborock.roborock_typing import RoborockCommand

_ENABLED_PARAM = "enabled"


class ValleyElectricityTimerTrait(ValleyElectricityTimer, common.V1TraitMixin):
    """Trait for managing Valley Electricity Timer settings on Roborock devices."""

    command = RoborockCommand.GET_VALLEY_ELECTRICITY_TIMER
    requires_feature = "is_supported_valley_electricity"

    @property
    def is_on(self) -> bool:
        """Return whether the Valley Electricity Timer is enabled."""
        return self.enabled == 1

    async def set_timer(self, timer: ValleyElectricityTimer) -> None:
        """Set the Valley Electricity Timer settings of the device."""
        await self.rpc_channel.send_command(RoborockCommand.SET_VALLEY_ELECTRICITY_TIMER, params=timer.as_dict())

    async def clear_timer(self) -> None:
        """Clear the Valley Electricity Timer settings of the device."""
        await self.rpc_channel.send_command(RoborockCommand.CLOSE_VALLEY_ELECTRICITY_TIMER)

    async def enable(self) -> None:
        """Enable the Valley Electricity Timer settings of the device."""
        await self.rpc_channel.send_command(
            RoborockCommand.SET_VALLEY_ELECTRICITY_TIMER,
            params={
                **self.as_dict(),
                _ENABLED_PARAM: 1,
            },
        )

    async def disable(self) -> None:
        """Disable the Valley Electricity Timer settings of the device."""
        await self.rpc_channel.send_command(
            RoborockCommand.SET_VALLEY_ELECTRICITY_TIMER,
            params={
                **self.as_dict(),
                _ENABLED_PARAM: 0,
            },
        )
