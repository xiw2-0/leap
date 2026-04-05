# QMT Quote Data Documentation

## Overview

QMT provides three main types of market data access methods, each serving different use cases:

1. **Local Data** - Historical data stored locally
2. **Full Push Data** - Real-time market snapshots without subscription limits  
3. **Subscription Data** - Real-time data with subscription-based access

---

## 1. Local Data (Historical)

### Description
- Downloaded historical market data stored as encrypted files on local disk
- Ideal for backtesting scenarios where you need historical price series
- Does not update in real-time during trading hours

### Key Functions
- `download_history_data2()` - Downloads historical data for specified time periods
- `get_local_data()` - Retrieves local historical data quickly
- `get_market_data_ex(subscribe=False)` - Can also be used to retrieve local data without subscribing

### Usage Notes
- **Incremental Downloads**: When start time is not specified, downloads incrementally from the last available local date
- **Manual Downloads**: When start time is specified, downloads exactly the requested period
- **Performance**: Fast access since data is stored locally
- **Limitation**: No real-time updates during market hours
- **Function Choice**: `get_local_data()` is optimized for pure local data access, while `get_market_data_ex(subscribe=False)` provides more flexibility but may have additional overhead

---

## 2. Full Push Data (Real-time Market Snapshots)

### Description  
- Automatically receives and updates real-time market snapshots for the entire market upon client startup
- Includes daily OHLCV data and Level-1 order book data (when enabled)
- **No subscription limits** - can access all market instruments
- **Server immediately forwards exchange data** and sends incremental updates to clients

### Key Functions
- `get_full_tick()` - Retrieves current latest values for all instruments at once
- `subscribe_whole_quote()` - Registers callback functions to handle incremental updates

### Characteristics
- **Update Frequency**: Updates every 50ms during market hours
- **Data Scope**: Full market coverage with only latest values (no historical data)
- **Performance**: Very fast due to pre-cached data in client
- **Level-1 Support**: Five-level tick available when enabled in settings

### Important Notes
- **Configuration Required**: Need to enable Level-1 行情 in QMT settings for Level 1 order book access

---

## 3. Subscription Data (Targeted Real-time)

### Description
- Subscribe to specific instruments and timeframes from the server
- Supports four basic periods: Tick, 1-minute, 5-minute, and Daily bars
- **Subscription limits apply** - maximum number of concurrent subscriptions

### Key Functions
- `subscribe_quote()` - Subscribe to specific instruments and timeframes
- `unsubscribe_quote()` - Unsubscribe using subscription ID to free up quota
- `get_market_data_ex()` - Get subscribed real-time data

### Subscription Limits & Management

#### Quota System
- **Total Limit**: Maximum ~300 subscriptions (example limit)
- **Period Counting**: Each timeframe counts separately
  - Example: Subscribing to Pudong Development Bank for 1-min, 5-min, and daily = 3 subscriptions
- **VIP Option**: Can purchase VIP service to increase subscription limits

#### Level-2 Considerations
- Level-2 subscriptions have separate limits from Level-1
- Level-1 and Level-2 quotas are independent of each other

### Best Practices

#### Recommended Approach
```python
# For large instrument sets (> subscription limit)
# Use combination approach:
# 1. download_history_data2() + get_local_data() for historical
# 2. get_full_tick() for real-time latest prices
```

---

## Function Comparison Guide

| Function | Purpose | Subscription Required | Historical Data | Real-time Updates | Limits |
|----------|---------|----------------------|-----------------|-------------------|---------|
| `download_history_data2()` | Download historical data | No | ✅ | ❌ | None |
| `get_local_data()` | Read local historical data | No | ✅ | ❌ | None |
| `get_market_data_ex(subscribe=False)` | Read local data with flexible parameters | No | ✅ | ❌ | None |
| `get_full_tick()` | Get latest market snapshot | No | ❌ | ✅ | None |
| `subscribe_quote()` | Subscribe to specific instruments | ✅ | Limited | ✅ | ~300 max |
| `get_market_data_ex(subscribe=True)` | Subscribe and get subscribed data | ✅ | Limited | ✅ | Subscription limits |

---

## Common Issues & Solutions

### Issue: Duplicate/Incorrect Data
**Symptom**: Returned data shows repeated values instead of real market movements  
**Cause**: Exceeded subscription quantity limits  
**Solution**: Reduce subscription count or upgrade to VIP service

### Issue: Missing Level-2 Data in Full Push
**Symptom**: `get_full_tick()` returns only latest price, no order book  
**Solution**: 
1. Enable Level-2行情 in QMT client settings
2. Or use `subscribe_quote()` with Level-2 permissions for specific instruments

### Issue: Slow Initial Subscription
**Symptom**: First `subscribe_quote()` call takes longer than subsequent calls  
**Cause**: Initial data synchronization with server  
**Solution**: This is normal behavior; subsequent updates are much faster

---

## Architecture Overview

### Data Centers
- **Market Data Center**: Controls individual subscriptions (`subscribe_quote`)
- **Trading Data Center**: Manages full push data (`get_full_tick`, `subscribe_whole_quote`)

### Performance Recommendations
- **Backtesting**: Use `download_history_data2()` + `get_local_data()` for best performance
- **Real-time Monitoring**: Use `get_full_tick()` for broad market coverage
- **Targeted Trading**: Use `subscribe_quote()` for specific instruments you're actively trading
- **Large Portfolios**: Combine approaches to stay within subscription limits

This structured approach helps you choose the right data access method based on your specific trading or analysis requirements while avoiding common pitfalls related to subscription limits and performance issues.