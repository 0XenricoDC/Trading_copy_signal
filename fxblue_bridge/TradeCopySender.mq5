//+------------------------------------------------------------------+
//|                                            TradeCopySender.mq5    |
//|                                      TradeCopy FX Blue Bridge     |
//|                          Monitors TradeCopy trades and sends      |
//|                          them to FX Blue for distribution         |
//+------------------------------------------------------------------+
#property copyright "TradeCopy"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

//--- Input parameters
input long     InpTradeCopyMagic = 123456789;          // TradeCopy Magic Number
input int      InpFxBlueMagic = 999999;                 // FX Blue Sender Magic Number
input bool     InpCopyToFxBlue = true;                  // Enable FX Blue copying
input double   InpLotMultiplier = 1.0;                  // Lot size multiplier
input bool     InpCopySL = true;                        // Copy Stop Loss
input bool     InpCopyTP = true;                        // Copy Take Profit
input int      InpMaxSlippage = 30;                     // Max slippage (points)
input bool     InpDebugMode = false;                    // Debug mode

//--- Global variables
CTrade         g_trade;
string         g_processedPositions = "";               // Comma-separated list of processed tickets

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("TradeCopySender initialized");
   Print("Monitoring TradeCopy trades with magic: ", InpTradeCopyMagic);
   Print("Sending to FX Blue with magic: ", InpFxBlueMagic);

   //--- Configure trade object
   g_trade.SetExpertMagicNumber(InpFxBlueMagic);
   g_trade.SetDeviationInPoints(InpMaxSlippage);
   g_trade.SetTypeFilling(ORDER_FILLING_IOC);

   //--- Set timer for monitoring
   EventSetTimer(1);

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("TradeCopySender stopped");
}

//+------------------------------------------------------------------+
//| Timer function - Monitor for new TradeCopy positions               |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!InpCopyToFxBlue) return;

   MonitorTradeCopyPositions();
   MonitorClosedPositions();
}

//+------------------------------------------------------------------+
//| Monitor for new TradeCopy positions to copy                        |
//+------------------------------------------------------------------+
void MonitorTradeCopyPositions()
{
   int totalPositions = PositionsTotal();

   for(int i = 0; i < totalPositions; i++)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == 0) continue;

      //--- Check if this is a TradeCopy trade
      long magic = PositionGetInteger(POSITION_MAGIC);

      if(magic != InpTradeCopyMagic) continue;

      //--- Check if already processed
      if(IsPositionProcessed(ticket)) continue;

      //--- Copy this position to FX Blue
      if(CopyPositionToFxBlue(ticket))
      {
         MarkPositionProcessed(ticket);
         Print("Copied TradeCopy position to FX Blue: Ticket #", ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| Monitor for closed TradeCopy positions                             |
//+------------------------------------------------------------------+
void MonitorClosedPositions()
{
   //--- Check history for recently closed positions
   datetime fromTime = TimeCurrent() - 60;  // Last minute
   datetime toTime = TimeCurrent();

   if(!HistorySelect(fromTime, toTime)) return;

   int totalDeals = HistoryDealsTotal();

   for(int i = 0; i < totalDeals; i++)
   {
      ulong dealTicket = HistoryDealGetTicket(i);

      if(dealTicket == 0) continue;

      //--- Check if this is a closing deal
      ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);

      if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY) continue;

      //--- Check if it's a TradeCopy trade
      long magic = HistoryDealGetInteger(dealTicket, DEAL_MAGIC);

      if(magic != InpTradeCopyMagic) continue;

      //--- Get the original position ticket
      ulong positionId = HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID);

      //--- Check if we need to close the corresponding FX Blue position
      string closeKey = "TC_CLOSE_" + IntegerToString(positionId);
      int closed = (int)GlobalVariableGet(closeKey);

      if(closed > 0) continue;

      //--- Find and close corresponding FX Blue position
      if(CloseCorrespondingFxBluePosition(positionId, dealTicket))
      {
         GlobalVariableSet(closeKey, 1);
         Print("Closed corresponding FX Blue position for: ", positionId);
      }
   }
}

//+------------------------------------------------------------------+
//| Copy a TradeCopy position to FX Blue                               |
//+------------------------------------------------------------------+
bool CopyPositionToFxBlue(ulong ticket)
{
   //--- Get position details
   if(!PositionSelectByTicket(ticket))
   {
      Print("ERROR: Could not select position ", ticket);
      return false;
   }

   string symbol = PositionGetString(POSITION_SYMBOL);
   long positionType = PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME) * InpLotMultiplier;
   double stopLoss = InpCopySL ? PositionGetDouble(POSITION_SL) : 0;
   double takeProfit = InpCopyTP ? PositionGetDouble(POSITION_TP) : 0;
   string comment = "TC:" + IntegerToString(ticket);

   //--- Normalize volume
   volume = NormalizeVolume(symbol, volume);

   if(volume <= 0)
   {
      Print("ERROR: Invalid volume for ", symbol);
      return false;
   }

   //--- Get current price
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
   {
      Print("ERROR: Could not get tick for ", symbol);
      return false;
   }

   //--- Open position
   bool result = false;

   if(positionType == POSITION_TYPE_BUY)
   {
      result = g_trade.Buy(volume, symbol, tick.ask, stopLoss, takeProfit, comment);
   }
   else if(positionType == POSITION_TYPE_SELL)
   {
      result = g_trade.Sell(volume, symbol, tick.bid, stopLoss, takeProfit, comment);
   }

   if(!result)
   {
      Print("ERROR: Failed to open FX Blue position. Error: ", g_trade.ResultRetcodeDescription());
      return false;
   }

   //--- Store mapping between original ticket and FX Blue ticket
   ulong fxBlueTicket = g_trade.ResultOrder();
   string mappingKey = "TC_MAP_" + IntegerToString(ticket);
   GlobalVariableSet(mappingKey, (double)fxBlueTicket);

   if(InpDebugMode)
   {
      Print("Opened FX Blue position: ", fxBlueTicket, " (copy of ", ticket, ")");
   }

   return true;
}

//+------------------------------------------------------------------+
//| Close corresponding FX Blue position                               |
//+------------------------------------------------------------------+
bool CloseCorrespondingFxBluePosition(ulong originalPositionId, ulong dealTicket)
{
   //--- Get the mapping to FX Blue ticket
   string mappingKey = "TC_MAP_" + IntegerToString(originalPositionId);
   double fxBlueTicketD = GlobalVariableGet(mappingKey);

   if(fxBlueTicketD == 0)
   {
      if(InpDebugMode)
      {
         Print("No FX Blue mapping found for position ", originalPositionId);
      }
      return false;
   }

   ulong fxBlueTicket = (ulong)fxBlueTicketD;

   //--- Find the FX Blue position with this ticket reference
   int totalPositions = PositionsTotal();

   for(int i = 0; i < totalPositions; i++)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == 0) continue;

      //--- Check magic number
      long magic = PositionGetInteger(POSITION_MAGIC);

      if(magic != InpFxBlueMagic) continue;

      //--- Check comment for original ticket reference
      string comment = PositionGetString(POSITION_COMMENT);

      if(StringFind(comment, "TC:" + IntegerToString(originalPositionId)) >= 0)
      {
         //--- Close this position
         if(g_trade.PositionClose(ticket))
         {
            if(InpDebugMode)
            {
               Print("Closed FX Blue position ", ticket);
            }
            return true;
         }
         else
         {
            Print("ERROR: Failed to close FX Blue position ", ticket, ": ", g_trade.ResultRetcodeDescription());
            return false;
         }
      }
   }

   //--- Try to find by stored order ticket
   for(int i = 0; i < totalPositions; i++)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == fxBlueTicket)
      {
         if(g_trade.PositionClose(ticket))
         {
            return true;
         }
      }
   }

   if(InpDebugMode)
   {
      Print("Could not find FX Blue position to close for ", originalPositionId);
   }

   return false;
}

//+------------------------------------------------------------------+
//| Check if position has been processed                               |
//+------------------------------------------------------------------+
bool IsPositionProcessed(ulong ticket)
{
   string key = "TC_SENT_" + IntegerToString(ticket);
   return GlobalVariableGet(key) > 0;
}

//+------------------------------------------------------------------+
//| Mark position as processed                                         |
//+------------------------------------------------------------------+
void MarkPositionProcessed(ulong ticket)
{
   string key = "TC_SENT_" + IntegerToString(ticket);
   GlobalVariableSet(key, 1);
}

//+------------------------------------------------------------------+
//| Normalize volume according to symbol specifications                |
//+------------------------------------------------------------------+
double NormalizeVolume(string symbol, double volume)
{
   double minVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double stepVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   //--- Clamp to min/max
   volume = MathMax(minVolume, MathMin(maxVolume, volume));

   //--- Round to step
   volume = MathFloor(volume / stepVolume) * stepVolume;

   return NormalizeDouble(volume, 2);
}

//+------------------------------------------------------------------+
//| Trade transaction handler                                          |
//+------------------------------------------------------------------+
void OnTradeTransaction(
   const MqlTradeTransaction& trans,
   const MqlTradeRequest& request,
   const MqlTradeResult& result)
{
   //--- Handle position modifications (SL/TP changes)
   if(trans.type == TRADE_TRANSACTION_POSITION && InpCopyToFxBlue)
   {
      //--- Check if this is a TradeCopy position
      if(PositionSelectByTicket(trans.position))
      {
         long magic = PositionGetInteger(POSITION_MAGIC);

         if(magic == InpTradeCopyMagic)
         {
            //--- Position was modified - sync SL/TP to FX Blue copy
            SyncPositionModification(trans.position);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Sync position modifications to FX Blue copy                        |
//+------------------------------------------------------------------+
void SyncPositionModification(ulong originalTicket)
{
   //--- Get the mapping to FX Blue
   string mappingKey = "TC_MAP_" + IntegerToString(originalTicket);
   double fxBlueTicketD = GlobalVariableGet(mappingKey);

   if(fxBlueTicketD == 0) return;

   //--- Get original position details
   if(!PositionSelectByTicket(originalTicket)) return;

   double newSL = PositionGetDouble(POSITION_SL);
   double newTP = PositionGetDouble(POSITION_TP);

   //--- Find FX Blue position
   int totalPositions = PositionsTotal();

   for(int i = 0; i < totalPositions; i++)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == 0) continue;

      long magic = PositionGetInteger(POSITION_MAGIC);

      if(magic != InpFxBlueMagic) continue;

      string comment = PositionGetString(POSITION_COMMENT);

      if(StringFind(comment, "TC:" + IntegerToString(originalTicket)) >= 0)
      {
         //--- Modify FX Blue position
         double currentSL = PositionGetDouble(POSITION_SL);
         double currentTP = PositionGetDouble(POSITION_TP);

         if(InpCopySL) newSL = (newSL > 0) ? newSL : currentSL;
         else newSL = currentSL;

         if(InpCopyTP) newTP = (newTP > 0) ? newTP : currentTP;
         else newTP = currentTP;

         if(newSL != currentSL || newTP != currentTP)
         {
            if(g_trade.PositionModify(ticket, newSL, newTP))
            {
               if(InpDebugMode)
               {
                  Print("Updated FX Blue position ", ticket, " SL/TP");
               }
            }
         }

         break;
      }
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- Timer-based monitoring is used instead
}
//+------------------------------------------------------------------+
