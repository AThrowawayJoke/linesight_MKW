from dolphin import memory
import mkw_config

from . import RegionError

class KartObjectManager:
    @staticmethod
    def chain() -> int:
        try:
            return memory.read_u32(mkw_config.address_id)
        except KeyError:
            raise RegionError

    @staticmethod
    def kart_object_arr() -> int:
        kart_obj_mgr_ref = KartObjectManager.chain()
        return memory.read_u32(kart_obj_mgr_ref + 0x20)

    @staticmethod
    def kart_object(player_idx=0) -> int:
        assert(0 <= player_idx < KartObjectManager.player_count())
        kart_obj_arr_ref = KartObjectManager.kart_object_arr()
        kart_obj_ptr = kart_obj_arr_ref + (player_idx * 0x4)
        return memory.read_u32(kart_obj_ptr)

    @staticmethod
    def player_count() -> int:
        """This is copied from RaceConfig->mRaceScenario.mPlayerCount."""
        return memory.read_u8(KartObjectManager.chain() + 0x24)

    @staticmethod
    def flags() -> int:
        kart_obj_mgr_ref = KartObjectManager.chain()
        flags_ref = kart_obj_mgr_ref + 0x28
        return memory.read_u32(flags_ref)