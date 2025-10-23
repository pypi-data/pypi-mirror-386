from .iroguelike_scroll_ending_text import IRoguelikeScrollEndingText


class RL04EndingText(IRoguelikeScrollEndingText):
    summaryGetFragment: str
    summaryUseIdea: str
    summaryUseFood: str
    summaryDropFragment: str
    summaryMeetDisaster: str
    summaryLeaveDisaster: str
    summaryEnterAlchemy: str
    summaryAlchemyOthers: str
    summaryAlchemyFragment: str
    summaryWeightOverweight: str
    summaryWeightLimit: str
    summaryWeightSafe: str
    summaryDuelWin: str
    summaryDuelTie: str
    summaryDuelLose: str
    summaryPermUpgrade: str
    summaryTempUpgrade: str
    summarySellFragment: str
    summaryMeetTrade: str
    summaryMeetSecretpath: str
    summaryExchangeRelic: str
    summaryMeetSpZone: str | None
    summaryBuyWithPriceId: str | None
    summaryStockRecruitTicket: str | None
    summaryExpeditionGo: str | None
    summaryExpeditionBack: str | None
    summaryFightWin: str | None = None
    summaryFightFail: str | None = None
