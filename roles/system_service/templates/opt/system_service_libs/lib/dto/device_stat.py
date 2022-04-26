from lib.dto._changeable import Changeable
from datetime import datetime


class DeviceStat(Changeable):
    def __init__(self, cache, mac):
        super().__init__(cache)
        
        self.mac = mac
        
        self.offline_since = datetime.now()
        
        # internal variables without change detection
        self.last_seen = datetime.now()

    def getMAC(self):
        return self.mac

    def getUnlockedDevice(self):
        return self._getCache().getUnlockedDevice(self.mac)
    
    def setOnline(self,flag):
        if flag:
            self.last_seen = datetime.now()
            offline_since = None
        else:
            offline_since = self.last_seen
        
        if self.offline_since != offline_since:
            self._markAsChanged( "online_state", "offline" if offline_since else "online")
            self.offline_since = offline_since
            
    def isOnline(self):
        return self.offline_since is None

    def getLastSeen(self):
        return self.last_seen

    def getSerializeable(self):
        _stat = {
            "mac": self.mac,
            "offline_since": self.offline_since.astimezone().isoformat('T') if self.offline_since is not None else None,
            "details": self._getDetails()
        }
            
        return _stat
            
    def __repr__(self):
        device = self._getCache().getUnlockedDevice(self.mac)
        return "{}".format(device if device is not None else self.mac)
