//+------------------------------------------------------------------+
//|                                          TradeCopyReceiver.mq5    |
//|                                      TradeCopy FX Blue Bridge     |
//|                          Receives trades from FX Blue and sends   |
//|                          HTTP POST to TradeCopy backend API       |
//+------------------------------------------------------------------+
#property copyright "TradeCopy"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

//--- Input parameters
input string   InpApiUrl = "http://localhost:8000";    // TradeCopy API URL
input string   InpApiKey = "";                          // API Key (optional)
input string   InpTenantId = "";                        // Tenant ID
input int      InpMagicNumber = 888888;                 // Magic number for FX Blue trades
input bool     InpDebugMode = false;                    // Debug mode

//--- Global variables
int            g_lastTicket = 0;
datetime       g_lastCheck = 0;
int            g_checkInterval = 1;                     // Check every second

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- Validate inputs
   if(StringLen(InpTenantId) == 0)
   {
      Print("ERROR: Tenant ID is required");
      return INIT_PARAMETERS_INCORRECT;
   }

   //--- Check WebRequest permissions
   if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))
   {
      Print("WARNING: DLL imports are disabled. Please enable in Tools > Options > Expert Advisors");
   }

   Print("TradeCopyReceiver initialized");
   Print("API URL: ", InpApiUrl);
   Print("Tenant ID: ", InpTenantId);
   Print("Monitoring trades with magic number: ", InpMagicNumber);

   //--- Set timer for checking new trades
   EventSetTimer(g_checkInterval);

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("TradeCopyReceiver stopped");
}

//+------------------------------------------------------------------+
//| Timer function - Check for new FX Blue trades                      |
//+------------------------------------------------------------------+
void OnTimer()
{
   CheckNewPositions();
}

//+------------------------------------------------------------------+
//| Check for new positions opened by FX Blue                          |
//+------------------------------------------------------------------+
void CheckNewPositions()
{
   int totalPositions = PositionsTotal();

   for(int i = 0; i < totalPositions; i++)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == 0) continue;

      //--- Check if this is an FX Blue trade (by magic number)
      long magic = PositionGetInteger(POSITION_MAGIC);

      if(magic != InpMagicNumber) continue;

      //--- Check if we already processed this trade
      string processedKey = "TC_PROCESSED_" + IntegerToString(ticket);
      int processed = (int)GlobalVariableGet(processedKey);

      if(processed > 0) continue;

      //--- New FX Blue trade detected - send to API
      if(SendTradeSignal(ticket))
      {
         //--- Mark as processed
         GlobalVariableSet(processedKey, 1);
         Print("Sent FX Blue trade to TradeCopy: Ticket #", ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| Send trade signal to TradeCopy API                                 |
//+------------------------------------------------------------------+
bool SendTradeSignal(ulong ticket)
{
   //--- Get position details
   if(!PositionSelectByTicket(ticket))
   {
      Print("ERROR: Could not select position ", ticket);
      return false;
   }

   string symbol = PositionGetString(POSITION_SYMBOL);
   long positionType = PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double stopLoss = PositionGetDouble(POSITION_SL);
   double takeProfit = PositionGetDouble(POSITION_TP);
   string comment = PositionGetString(POSITION_COMMENT);
   datetime openTime = (datetime)PositionGetInteger(POSITION_TIME);

   //--- Determine direction
   string direction = (positionType == POSITION_TYPE_BUY) ? "buy" : "sell";

   //--- Build JSON payload
   string json = BuildSignalJson(
      symbol,
      direction,
      volume,
      openPrice,
      stopLoss,
      takeProfit,
      comment,
      ticket,
      openTime
   );

   if(InpDebugMode)
   {
      Print("Sending JSON: ", json);
   }

   //--- Send HTTP POST
   return SendHttpPost("/api/v1/signals/fxblue-webhook", json);
}

//+------------------------------------------------------------------+
//| Build JSON payload for signal                                      |
//+------------------------------------------------------------------+
string BuildSignalJson(
   string symbol,
   string direction,
   double volume,
   double openPrice,
   double stopLoss,
   double takeProfit,
   string comment,
   ulong ticket,
   datetime openTime)
{
   string json = "{";
   json += "\"tenant_id\":\"" + InpTenantId + "\",";
   json += "\"source\":\"fxblue\",";
   json += "\"symbol\":\"" + symbol + "\",";
   json += "\"direction\":\"" + direction + "\",";
   json += "\"volume\":" + DoubleToString(volume, 2) + ",";
   json += "\"entry_price\":" + DoubleToString(openPrice, 5) + ",";

   if(stopLoss > 0)
   {
      json += "\"stop_loss\":" + DoubleToString(stopLoss, 5) + ",";
   }

   if(takeProfit > 0)
   {
      json += "\"take_profit\":" + DoubleToString(takeProfit, 5) + ",";
   }

   json += "\"source_ticket\":" + IntegerToString(ticket) + ",";
   json += "\"comment\":\"" + EscapeJsonString(comment) + "\",";
   json += "\"timestamp\":\"" + TimeToString(openTime, TIME_DATE|TIME_SECONDS) + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Send HTTP POST request                                             |
//+------------------------------------------------------------------+
bool SendHttpPost(string endpoint, string jsonData)
{
   string url = InpApiUrl + endpoint;
   string headers = "Content-Type: application/json\r\n";

   if(StringLen(InpApiKey) > 0)
   {
      headers += "Authorization: Bearer " + InpApiKey + "\r\n";
   }

   char postData[];
   char result[];
   string resultHeaders;

   //--- Convert string to char array
   StringToCharArray(jsonData, postData, 0, StringLen(jsonData), CP_UTF8);

   //--- Resize to remove null terminator
   ArrayResize(postData, StringLen(jsonData));

   //--- Send request
   int timeout = 5000;  // 5 seconds

   int responseCode = WebRequest(
      "POST",
      url,
      headers,
      timeout,
      postData,
      result,
      resultHeaders
   );

   if(responseCode == -1)
   {
      int error = GetLastError();
      Print("ERROR: WebRequest failed. Error code: ", error);
      Print("Make sure ", InpApiUrl, " is in the allowed URLs list (Tools > Options > Expert Advisors)");
      return false;
   }

   if(responseCode != 200 && responseCode != 201)
   {
      string response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
      Print("ERROR: API returned status ", responseCode, ": ", response);
      return false;
   }

   if(InpDebugMode)
   {
      string response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
      Print("API Response: ", response);
   }

   return true;
}

//+------------------------------------------------------------------+
//| Escape special characters for JSON string                          |
//+------------------------------------------------------------------+
string EscapeJsonString(string str)
{
   string result = str;

   StringReplace(result, "\\", "\\\\");
   StringReplace(result, "\"", "\\\"");
   StringReplace(result, "\n", "\\n");
   StringReplace(result, "\r", "\\r");
   StringReplace(result, "\t", "\\t");

   return result;
}

//+------------------------------------------------------------------+
//| Expert tick function (not used, timer-based)                       |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- We use timer instead of tick for consistent checking
}

//+------------------------------------------------------------------+
//| Trade transaction handler - immediate detection                    |
//+------------------------------------------------------------------+
void OnTradeTransaction(
   const MqlTradeTransaction& trans,
   const MqlTradeRequest& request,
   const MqlTradeResult& result)
{
   //--- Check for new deal (position opened)
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      //--- Check if this might be an FX Blue trade
      if(trans.deal > 0)
      {
         //--- Select the deal to get its properties
         if(HistoryDealSelect(trans.deal))
         {
            long magic = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);

            if(magic == InpMagicNumber)
            {
               Print("FX Blue deal detected: ", trans.deal);
               //--- The position will be processed on next timer tick
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
