# ============================================================
# ivolatility_backtesting.py - ENHANCED VERSION
# 
# NEW FEATURES:
# 1. Combined stop-loss (requires BOTH conditions)
# 2. Parameter optimization framework
# 3. Optimization results visualization
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import ivolatility as ivol
import os
import time
import psutil
import warnings
from itertools import product
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', message='.*SettingWithCopyWarning.*')
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (15, 8)

def create_optimization_folder(base_dir='optimization_results'):
    """
    Create timestamped folder for optimization run
    Returns: folder path (e.g., 'optimization_results/20250122_143025')
    """
    from pathlib import Path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_path = Path(base_dir) / timestamp
    folder_path.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Created optimization folder: {folder_path}")
    return str(folder_path)

# ============================================================
# RESOURCE MONITOR
# ============================================================
class ResourceMonitor:
    """Monitor CPU and RAM with container support"""
    
    def __init__(self, show_container_total=False):
        self.process = psutil.Process()
        self.cpu_count = psutil.cpu_count()
        self.last_cpu_time = None
        self.last_check_time = None
        self.use_cgroups = self._check_cgroups_v2()
        self.show_container_total = show_container_total
        self.cpu_history = []
        self.cpu_history_max = 5
        
        if self.use_cgroups:
            quota = self._read_cpu_quota()
            if quota and quota > 0:
                self.cpu_count = quota
        
        self.context = "Container" if self.use_cgroups else "Host"
        
    def _read_cpu_quota(self):
        try:
            with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                line = f.read().strip()
                if line == 'max':
                    return None
                parts = line.split()
                if len(parts) == 2:
                    quota = int(parts[0])
                    period = int(parts[1])
                    return quota / period
        except:
            pass
        return None
        
    def get_context_info(self):
        if self.use_cgroups:
            current, max_mem = self._read_cgroup_memory()
            ram_info = ""
            if max_mem:
                max_mem_gb = max_mem / (1024**3)
                ram_info = f", {max_mem_gb:.1f}GB limit"
            
            mem_type = "container total" if self.show_container_total else "process only"
            return f"Container (CPU: {self.cpu_count:.1f} cores{ram_info}) - RAM: {mem_type}"
        else:
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            return f"Host ({self.cpu_count} cores, {total_ram_gb:.0f}GB RAM) - RAM: process"
        
    def _check_cgroups_v2(self):
        try:
            return os.path.exists('/sys/fs/cgroup/cpu.stat') and \
                   os.path.exists('/sys/fs/cgroup/memory.current')
        except:
            return False
    
    def _read_cgroup_cpu(self):
        try:
            with open('/sys/fs/cgroup/cpu.stat', 'r') as f:
                for line in f:
                    if line.startswith('usage_usec'):
                        return int(line.split()[1])
        except:
            pass
        return None
    
    def _read_cgroup_memory(self):
        try:
            with open('/sys/fs/cgroup/memory.current', 'r') as f:
                current = int(f.read().strip())
            with open('/sys/fs/cgroup/memory.max', 'r') as f:
                max_mem = f.read().strip()
                if max_mem == 'max':
                    max_mem = psutil.virtual_memory().total
                else:
                    max_mem = int(max_mem)
            return current, max_mem
        except:
            pass
        return None, None
    
    def get_cpu_percent(self):
        if self.use_cgroups:
            current_time = time.time()
            current_cpu = self._read_cgroup_cpu()
            
            if current_cpu and self.last_cpu_time and self.last_check_time:
                time_delta = current_time - self.last_check_time
                cpu_delta = current_cpu - self.last_cpu_time
                
                if time_delta > 0:
                    cpu_percent = (cpu_delta / (time_delta * 1_000_000)) * 100
                    cpu_percent = min(cpu_percent, 100 * self.cpu_count)
                    
                    self.cpu_history.append(cpu_percent)
                    if len(self.cpu_history) > self.cpu_history_max:
                        self.cpu_history.pop(0)
                    
                    self.last_cpu_time = current_cpu
                    self.last_check_time = current_time
                    
                    return round(sum(self.cpu_history) / len(self.cpu_history), 1)
            
            self.last_cpu_time = current_cpu
            self.last_check_time = current_time
        
        try:
            cpu = self.process.cpu_percent(interval=0.1)
            if cpu == 0:
                cpu = psutil.cpu_percent(interval=0.1)
            
            self.cpu_history.append(cpu)
            if len(self.cpu_history) > self.cpu_history_max:
                self.cpu_history.pop(0)
            
            return round(sum(self.cpu_history) / len(self.cpu_history), 1)
        except:
            return 0.0
    
    def get_memory_info(self):
        try:
            mem = self.process.memory_info()
            process_mb = mem.rss / (1024 * 1024)
            
            if self.use_cgroups:
                current, max_mem = self._read_cgroup_memory()
                if max_mem:
                    process_percent = (mem.rss / max_mem) * 100
                    
                    if current:
                        container_mb = current / (1024 * 1024)
                        container_percent = (current / max_mem) * 100
                        return (
                            round(process_mb, 1), 
                            round(process_percent, 1),
                            round(container_mb, 1),
                            round(container_percent, 1)
                        )
                    
                    return (
                        round(process_mb, 1), 
                        round(process_percent, 1),
                        round(process_mb, 1),
                        round(process_percent, 1)
                    )
            
            total = psutil.virtual_memory().total
            percent = (mem.rss / total) * 100
            
            return (
                round(process_mb, 1), 
                round(percent, 1),
                round(process_mb, 1),
                round(percent, 1)
            )
            
        except:
            return 0.0, 0.0, 0.0, 0.0


def create_progress_bar(reuse_existing=None):
    """Create or reuse enhanced progress bar"""
    if reuse_existing is not None:
        progress_bar, status_label, monitor, start_time = reuse_existing
        progress_bar.value = 0
        progress_bar.bar_style = 'info'
        status_label.value = "<b style='color:#0066cc'>Starting...</b>"
        return progress_bar, status_label, monitor, time.time()
    
    try:
        from IPython.display import display
        import ipywidgets as widgets
        
        progress_bar = widgets.FloatProgress(
            value=0, min=0, max=100,
            description='Progress:',
            bar_style='info',
            style={'bar_color': '#00ff00'},
            layout=widgets.Layout(width='100%', height='30px')
        )
        
        status_label = widgets.HTML(
            value="<b style='color:#0066cc'>Starting...</b>"
        )
        
        display(widgets.VBox([progress_bar, status_label]))
        
        monitor = ResourceMonitor()
        start_time = time.time()
        
        return progress_bar, status_label, monitor, start_time
    except ImportError:
        print("Warning: ipywidgets not available. Progress bar disabled.")
        return None, None, ResourceMonitor(), time.time()


def update_progress(progress_bar, status_label, monitor, current, total, start_time, message="Processing"):
    """Update progress bar with ETA, CPU%, RAM"""
    if progress_bar is None or status_label is None:
        return
    
    progress = (current / total) * 100
    progress_bar.value = progress
    
    elapsed = time.time() - start_time
    if current > 0:
        eta_seconds = (elapsed / current) * (total - current)
        eta_str = format_time(eta_seconds)
    else:
        eta_str = "calculating..."
    
    cpu = monitor.get_cpu_percent()
    process_mb, process_pct, container_mb, container_pct = monitor.get_memory_info()
    
    if abs(container_mb - process_mb) > 10:
        ram_display = (
            f"RAM: <span style='color:#4CAF50'>{process_mb}MB ({process_pct}%)</span> Python | "
            f"<span style='color:#2196F3'>{container_mb}MB ({container_pct}%)</span> Container"
        )
    else:
        ram_display = f"RAM: {process_mb}MB ({process_pct}%)"
    
    context_info = monitor.get_context_info()

    elapsed_str = format_time(elapsed)
    start_time_str = datetime.fromtimestamp(start_time).strftime('%H:%M:%S')
    
    status_label.value = (
        f"<b style='color:#0066cc'>{message} ({current}/{total})</b><br>"
        f"<span style='color:#666'>⏱️ Elapsed: {elapsed_str} | ETA: {eta_str} | Started: {start_time_str}</span><br>"
        f"<span style='color:#666'>CPU: {cpu}% | {ram_display}</span><br>"
        f"<span style='color:#999;font-size:10px'>{context_info}</span>"
    )


def format_time(seconds):
    """Format seconds to human readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ============================================================
# API HELPER
# ============================================================
class APIHelper:
    """Normalizes API responses"""
    
    @staticmethod
    def normalize_response(response, debug=False):
        if response is None:
            if debug:
                print("[APIHelper] Response is None")
            return None
        
        if isinstance(response, dict):
            if 'data' in response:
                if debug:
                    print(f"[APIHelper] Dict response: {len(response['data'])} records")
                return response
            else:
                if debug:
                    print("[APIHelper] Dict without 'data' key")
                return None
        
        if isinstance(response, pd.DataFrame):
            if response.empty:
                if debug:
                    print("[APIHelper] Empty DataFrame")
                return None
            
            records = response.to_dict('records')
            if debug:
                print(f"[APIHelper] DataFrame converted: {len(records)} records")
            return {'data': records, 'status': 'success'}
        
        if debug:
            print(f"[APIHelper] Unexpected type: {type(response)}")
        return None


class APIManager:
    """Centralized API key management"""
    _api_key = None
    _methods = {}
    
    @classmethod
    def initialize(cls, api_key):
        if not api_key:
            raise ValueError("API key cannot be empty")
        cls._api_key = api_key
        ivol.setLoginParams(apiKey=api_key)
        print(f"[API] Initialized: {api_key[:10]}...{api_key[-5:]}")
    
    @classmethod
    def get_method(cls, endpoint):
        if cls._api_key is None:
            api_key = os.getenv("API_KEY")
            if not api_key:
                raise ValueError("API key not set. Call init_api(key) first")
            cls.initialize(api_key)
        
        if endpoint not in cls._methods:
            ivol.setLoginParams(apiKey=cls._api_key)
            cls._methods[endpoint] = ivol.setMethod(endpoint)
        
        return cls._methods[endpoint]


def init_api(api_key=None):
    """Initialize IVolatility API"""
    if api_key is None:
        api_key = os.getenv("API_KEY")
    APIManager.initialize(api_key)


def api_call(endpoint, debug=False, **kwargs):
    """Make API call with automatic response normalization"""
    try:
        if debug and APIManager._api_key:
            base_url = "https://restapi.ivolatility.com"
            url_params = {}
            for key, value in kwargs.items():
                clean_key = key.rstrip('_') if key.endswith('_') else key
                url_params[clean_key] = value
            
            params_str = "&".join([f"{k}={v}" for k, v in url_params.items()])
            full_url = f"{base_url}{endpoint}?apiKey={APIManager._api_key}&{params_str}"
            print(f"\n[API] Full URL:")
            print(f"[API] {full_url}\n")
        
        method = APIManager.get_method(endpoint)
        response = method(**kwargs)
        
        normalized = APIHelper.normalize_response(response, debug=debug)
        
        if normalized is None and debug:
            print(f"[api_call] Failed to get data")
            print(f"[api_call] Endpoint: {endpoint}")
            print(f"[api_call] Params: {kwargs}")
        
        return normalized
    
    except Exception as e:
        if debug:
            print(f"[api_call] Exception: {e}")
            print(f"[api_call] Endpoint: {endpoint}")
            print(f"[api_call] Params: {kwargs}")
        return None


# ============================================================
# BACKTEST RESULTS
# ============================================================
class BacktestResults:
    """Universal container for backtest results"""
    
    def __init__(self, equity_curve, equity_dates, trades, initial_capital, 
                 config, benchmark_prices=None, benchmark_symbol='SPY',
                 daily_returns=None, debug_info=None):
        
        self.equity_curve = equity_curve
        self.equity_dates = equity_dates
        self.trades = trades
        self.initial_capital = initial_capital
        self.final_capital = equity_curve[-1] if len(equity_curve) > 0 else initial_capital
        self.config = config
        self.benchmark_prices = benchmark_prices
        self.benchmark_symbol = benchmark_symbol
        self.debug_info = debug_info if debug_info else []
        
        if daily_returns is None and len(equity_curve) > 1:
            self.daily_returns = [
                (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                for i in range(1, len(equity_curve))
            ]
        else:
            self.daily_returns = daily_returns if daily_returns else []
        
        self.max_drawdown = self._calculate_max_drawdown()
    
    def _calculate_max_drawdown(self):
        if len(self.equity_curve) < 2:
            return 0
        running_max = np.maximum.accumulate(self.equity_curve)
        drawdowns = (np.array(self.equity_curve) - running_max) / running_max * 100
        return abs(np.min(drawdowns))


# ============================================================
# STOP-LOSS MANAGER (ENHANCED VERSION WITH COMBINED STOP)
# ============================================================
class StopLossManager:
    """
    Enhanced stop-loss manager with COMBINED STOP support
    
    NEW STOP TYPE:
    - combined: Requires BOTH pl_loss AND directional conditions (from code 2)
    """
    
    def __init__(self):
        self.positions = {}
    
    def add_position(self, position_id, entry_price, entry_date, stop_type='fixed_pct', 
                    stop_value=0.05, atr=None, trailing_distance=None, use_pnl_pct=False,
                    is_short_bias=False, **kwargs):
        """
        Add position with stop-loss
        
        NEW for combined stop:
            stop_type='combined'
            stop_value={'pl_loss': 0.05, 'directional': 0.03}
        """
        self.positions[position_id] = {
            'entry_price': entry_price,
            'entry_date': entry_date,
            'stop_type': stop_type,
            'stop_value': stop_value,
            'atr': atr,
            'trailing_distance': trailing_distance,
            'highest_price': entry_price if not use_pnl_pct else 0,
            'lowest_price': entry_price if not use_pnl_pct else 0,
            'max_profit': 0,
            'use_pnl_pct': use_pnl_pct,
            'is_short_bias': is_short_bias,
            **kwargs  # Store additional parameters for combined stop
        }
    
    def check_stop(self, position_id, current_price, current_date, position_type='LONG', **kwargs):
        """
        Check if stop-loss triggered
        
        NEW: Supports 'combined' stop type
        """
        if position_id not in self.positions:
            return False, None, None
        
        pos = self.positions[position_id]
        stop_type = pos['stop_type']
        use_pnl_pct = pos.get('use_pnl_pct', False)
        
        # Update tracking
        if use_pnl_pct:
            pnl_pct = current_price
            pos['highest_price'] = max(pos['highest_price'], pnl_pct)
            pos['lowest_price'] = min(pos['lowest_price'], pnl_pct)
            pos['max_profit'] = max(pos['max_profit'], pnl_pct)
        else:
            if position_type == 'LONG':
                pos['highest_price'] = max(pos['highest_price'], current_price)
                current_profit = current_price - pos['entry_price']
            else:
                pos['lowest_price'] = min(pos['lowest_price'], current_price)
                current_profit = pos['entry_price'] - current_price
            
            pos['max_profit'] = max(pos['max_profit'], current_profit)
        
        # Route to appropriate check method
        if stop_type == 'fixed_pct':
            if use_pnl_pct:
                return self._check_fixed_pct_stop_pnl(pos, current_price)
            else:
                return self._check_fixed_pct_stop(pos, current_price, position_type)
        
        elif stop_type == 'trailing':
            if use_pnl_pct:
                return self._check_trailing_stop_pnl(pos, current_price)
            else:
                return self._check_trailing_stop(pos, current_price, position_type)
        
        elif stop_type == 'time_based':
            return self._check_time_stop(pos, current_date)
        
        elif stop_type == 'volatility':
            return self._check_volatility_stop(pos, current_price, position_type)
        
        elif stop_type == 'pl_loss':
            return self._check_pl_loss_stop(pos, kwargs)
        
        elif stop_type == 'directional':
            return self._check_directional_stop(pos, kwargs)
        
        # NEW: COMBINED STOP (requires BOTH conditions)
        elif stop_type == 'combined':
            return self._check_combined_stop(pos, kwargs)
        
        else:
            return False, None, None
    
    # ========================================================
    # EXISTING STOP METHODS (unchanged)
    # ========================================================
    
    def _check_fixed_pct_stop(self, pos, current_price, position_type):
        """Fixed percentage stop-loss (price-based)"""
        entry = pos['entry_price']
        stop_pct = pos['stop_value']
        
        if position_type == 'LONG':
            stop_level = entry * (1 - stop_pct)
            triggered = current_price <= stop_level
        else:
            stop_level = entry * (1 + stop_pct)
            triggered = current_price >= stop_level
        
        return triggered, stop_level, 'fixed_pct'
    
    def _check_fixed_pct_stop_pnl(self, pos, pnl_pct):
        """Fixed percentage stop-loss (P&L%-based for options)"""
        stop_pct = pos['stop_value']
        stop_level = -stop_pct * 100
        
        triggered = pnl_pct <= stop_level
        
        return triggered, stop_level, 'fixed_pct'
    
    def _check_trailing_stop(self, pos, current_price, position_type):
        """Trailing stop-loss (price-based)"""
        if pos['trailing_distance'] is None:
            pos['trailing_distance'] = pos['stop_value']
        
        distance = pos['trailing_distance']
        
        if position_type == 'LONG':
            stop_level = pos['highest_price'] * (1 - distance)
            triggered = current_price <= stop_level
        else:
            stop_level = pos['lowest_price'] * (1 + distance)
            triggered = current_price >= stop_level
        
        return triggered, stop_level, 'trailing'
    
    def _check_trailing_stop_pnl(self, pos, pnl_pct):
        """Trailing stop-loss (P&L%-based for options)"""
        if pos['trailing_distance'] is None:
            pos['trailing_distance'] = pos['stop_value']
        
        distance = pos['trailing_distance'] * 100
        
        stop_level = pos['highest_price'] - distance
        
        triggered = pnl_pct <= stop_level
        
        return triggered, stop_level, 'trailing'
    
    def _check_time_stop(self, pos, current_date):
        """Time-based stop"""
        days_held = (current_date - pos['entry_date']).days
        max_days = pos['stop_value']
        
        triggered = days_held >= max_days
        return triggered, None, 'time_based'
    
    def _check_volatility_stop(self, pos, current_price, position_type):
        """ATR-based stop"""
        if pos['atr'] is None:
            return False, None, None
        
        entry = pos['entry_price']
        atr_multiplier = pos['stop_value']
        stop_distance = pos['atr'] * atr_multiplier
        
        if position_type == 'LONG':
            stop_level = entry - stop_distance
            triggered = current_price <= stop_level
        else:
            stop_level = entry + stop_distance
            triggered = current_price >= stop_level
        
        return triggered, stop_level, 'volatility'
    
    def _check_pl_loss_stop(self, pos, kwargs):
        """Stop-loss based on actual P&L"""
        pnl_pct = kwargs.get('pnl_pct')
        
        if pnl_pct is None:
            current_pnl = kwargs.get('current_pnl', 0)
            total_cost = kwargs.get('total_cost', pos.get('total_cost', 1))
            
            if total_cost > 0:
                pnl_pct = (current_pnl / total_cost) * 100
            else:
                pnl_pct = 0
        
        stop_threshold = -pos['stop_value'] * 100
        triggered = pnl_pct <= stop_threshold
        
        return triggered, stop_threshold, 'pl_loss'
    
    def _check_directional_stop(self, pos, kwargs):
        """Stop-loss based on underlying price movement"""
        underlying_change_pct = kwargs.get('underlying_change_pct')
        
        if underlying_change_pct is None:
            current = kwargs.get('underlying_price')
            entry = kwargs.get('underlying_entry_price', pos.get('underlying_entry_price'))
            
            if current is not None and entry is not None and entry != 0:
                underlying_change_pct = ((current - entry) / entry) * 100
            else:
                underlying_change_pct = 0
        
        threshold = pos['stop_value'] * 100
        is_short_bias = pos.get('is_short_bias', False)
        
        if is_short_bias:
            triggered = underlying_change_pct >= threshold
        else:
            triggered = underlying_change_pct <= -threshold
        
        return triggered, threshold, 'directional'
    
    # ========================================================
    # NEW: COMBINED STOP (REQUIRES BOTH CONDITIONS)
    # ========================================================
    
    def _check_combined_stop(self, pos, kwargs):
        """
        Combined stop: Requires BOTH pl_loss AND directional conditions
        
        This is the key feature from code 2:
        - Must have P&L loss > threshold
        - AND underlying must move adversely > threshold
        
        Args:
            pos: Position dict with stop_value = {'pl_loss': 0.05, 'directional': 0.03}
            kwargs: Must contain pnl_pct and underlying_change_pct
        
        Returns:
            tuple: (triggered, thresholds_dict, 'combined')
        """
        stop_config = pos['stop_value']
        
        if not isinstance(stop_config, dict):
            # Fallback: treat as simple fixed stop
            return False, None, 'combined'
        
        pl_threshold = stop_config.get('pl_loss', 0.05)
        dir_threshold = stop_config.get('directional', 0.03)
        
        # Check P&L condition
        pnl_pct = kwargs.get('pnl_pct', 0)
        is_losing = pnl_pct <= (-pl_threshold * 100)
        
        # Check directional condition
        underlying_change_pct = kwargs.get('underlying_change_pct')
        
        if underlying_change_pct is None:
            current = kwargs.get('underlying_price')
            entry = kwargs.get('underlying_entry_price', pos.get('underlying_entry_price'))
            
            if current is not None and entry is not None and entry != 0:
                underlying_change_pct = ((current - entry) / entry) * 100
            else:
                underlying_change_pct = 0
        
        is_short_bias = pos.get('is_short_bias', False)
        
        if is_short_bias:
            # Bearish position: adverse move is UP
            adverse_move = underlying_change_pct >= (dir_threshold * 100)
        else:
            # Bullish position: adverse move is DOWN
            adverse_move = underlying_change_pct <= (-dir_threshold * 100)
        
        # CRITICAL: Both conditions must be true
        triggered = is_losing and adverse_move
        
        # Return detailed thresholds for reporting
        thresholds = {
            'pl_threshold': -pl_threshold * 100,
            'dir_threshold': dir_threshold * 100,
            'actual_pnl_pct': pnl_pct,
            'actual_underlying_change': underlying_change_pct,
            'pl_condition': is_losing,
            'dir_condition': adverse_move
        }
        
        return triggered, thresholds, 'combined'
    
    # ========================================================
    # UTILITY METHODS
    # ========================================================
    
    def remove_position(self, position_id):
        """Remove position from tracking"""
        if position_id in self.positions:
            del self.positions[position_id]
    
    def get_position_info(self, position_id):
        """Get position stop-loss info"""
        if position_id not in self.positions:
            return None
        
        pos = self.positions[position_id]
        return {
            'stop_type': pos['stop_type'],
            'stop_value': pos['stop_value'],
            'max_profit_before_stop': pos['max_profit']
        }


# ============================================================
# POSITION MANAGER (unchanged but compatible with combined stop)
# ============================================================
class PositionManager:
    """Universal Position Manager with automatic mode detection"""
    
    def __init__(self, config, debug=False):
        self.positions = {}
        self.closed_trades = []
        self.config = config
        self.debug = debug
        
        self.sl_enabled = config.get('stop_loss_enabled', False)
        if self.sl_enabled:
            self.sl_config = config.get('stop_loss_config', {})
            self.sl_manager = StopLossManager()
        else:
            self.sl_config = None
            self.sl_manager = None
    
    def open_position(self, position_id, symbol, entry_date, entry_price, 
                      quantity, position_type='LONG', **kwargs):
        """Open position with automatic stop-loss"""
        
        if entry_price == 0 and self.sl_enabled:
            if 'total_cost' not in kwargs or kwargs['total_cost'] == 0:
                raise ValueError(
                    f"\n{'='*70}\n"
                    f"ERROR: P&L% mode requires 'total_cost' parameter\n"
                    f"{'='*70}\n"
                )
        
        position = {
            'id': position_id,
            'symbol': symbol,
            'entry_date': entry_date,
            'entry_price': entry_price,
            'quantity': quantity,
            'type': position_type,
            'highest_price': entry_price,
            'lowest_price': entry_price,
            **kwargs
        }
        
        self.positions[position_id] = position
        
        if self.sl_enabled and self.sl_manager:
            sl_type = self.sl_config.get('type', 'fixed_pct')
            sl_value = self.sl_config.get('value', 0.05)
            
            use_pnl_pct = (entry_price == 0)
            is_short_bias = kwargs.get('is_short_bias', False)
            
            # Pass underlying_entry_price for combined stop
            self.sl_manager.add_position(
                position_id=position_id,
                entry_price=entry_price,
                entry_date=entry_date,
                stop_type=sl_type,
                stop_value=sl_value,
                atr=kwargs.get('atr', None),
                trailing_distance=self.sl_config.get('trailing_distance', None),
                use_pnl_pct=use_pnl_pct,
                is_short_bias=is_short_bias,
                underlying_entry_price=kwargs.get('entry_stock_price')  # For combined stop
            )
        
        if self.debug:
            mode = "P&L%" if entry_price == 0 else "Price"
            bias = " (SHORT BIAS)" if kwargs.get('is_short_bias') else ""
            print(f"[PositionManager] OPEN {position_id}: {symbol} @ {entry_price} (Mode: {mode}{bias})")
        
        return position
    
    def check_positions(self, current_date, price_data):
        """Check all positions for stop-loss triggers"""
        if not self.sl_enabled:
            return []
        
        to_close = []
        
        for position_id, position in self.positions.items():
            if position_id not in price_data:
                continue
            
            if isinstance(price_data[position_id], dict):
                data = price_data[position_id]
                current_price = data.get('price', position['entry_price'])
                current_pnl = data.get('pnl', 0)
                current_pnl_pct = data.get('pnl_pct', 0)
                
                # NEW: Pass underlying data for combined stop
                underlying_price = data.get('underlying_price')
                underlying_entry_price = data.get('underlying_entry_price')
                underlying_change_pct = data.get('underlying_change_pct')
            else:
                current_price = price_data[position_id]
                current_pnl = (current_price - position['entry_price']) * position['quantity']
                current_pnl_pct = (current_price - position['entry_price']) / position['entry_price'] if position['entry_price'] != 0 else 0
                underlying_price = None
                underlying_entry_price = None
                underlying_change_pct = None
            
            position['highest_price'] = max(position['highest_price'], current_price)
            position['lowest_price'] = min(position['lowest_price'], current_price)
            
            if position['entry_price'] == 0:
                check_value = current_pnl_pct
            else:
                check_value = current_price
            
            # Pass all data to stop manager
            stop_kwargs = {
                'pnl_pct': current_pnl_pct,
                'current_pnl': current_pnl,
                'total_cost': position.get('total_cost', 1),
                'underlying_price': underlying_price,
                'underlying_entry_price': underlying_entry_price or position.get('entry_stock_price'),
                'underlying_change_pct': underlying_change_pct
            }
            
            triggered, stop_level, stop_type = self.sl_manager.check_stop(
                position_id=position_id,
                current_price=check_value,
                current_date=current_date,
                position_type=position['type'],
                **stop_kwargs
            )
            
            if triggered:
                to_close.append({
                    'position_id': position_id,
                    'symbol': position['symbol'], 
                    'stop_type': stop_type,
                    'stop_level': stop_level,
                    'current_price': current_price,
                    'pnl': current_pnl,
                    'pnl_pct': current_pnl_pct
                })
                
                if self.debug:
                    mode = "P&L%" if position['entry_price'] == 0 else "Price"
                    print(f"[PositionManager] STOP-LOSS: {position_id} ({stop_type}, {mode}) @ {check_value:.2f}")
        
        return to_close
    
    def close_position(self, position_id, exit_date, exit_price, 
                       close_reason='manual', pnl=None, **kwargs):
        """Close position"""
        if position_id not in self.positions:
            if self.debug:
                print(f"[PositionManager] WARNING: Position {position_id} not found")
            return None
        
        position = self.positions.pop(position_id)
        
        if pnl is None:
            pnl = (exit_price - position['entry_price']) * position['quantity']
        
        if position['entry_price'] != 0:
            pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
        else:
            if 'total_cost' in position and position['total_cost'] != 0:
                pnl_pct = (pnl / position['total_cost']) * 100
            elif 'total_cost' in kwargs and kwargs['total_cost'] != 0:
                pnl_pct = (pnl / kwargs['total_cost']) * 100
            else:
                pnl_pct = 0.0        
                
        trade = {
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'symbol': position['symbol'],
            'signal': position['type'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'pnl': pnl,
            'return_pct': pnl_pct,
            'exit_reason': close_reason,
            'stop_type': self.sl_config.get('type', 'none') if self.sl_enabled else 'none',
            **kwargs
        }
        
        for key in ['call_strike', 'put_strike', 'expiration', 'contracts', 
                    'short_strike', 'long_strike', 'opt_type', 'spread_type',
                    'entry_z_score', 'is_short_bias', 'entry_lean', 'exit_lean',
                    'call_iv_entry', 'put_iv_entry', 'iv_lean_entry']:
            if key in position:
                trade[key] = position[key]
        
        for key in ['short_entry_bid', 'short_entry_ask', 'short_entry_mid',
                    'long_entry_bid', 'long_entry_ask', 'long_entry_mid',
                    'underlying_entry_price']:
            if key in position:
                trade[key] = position[key]
        
        for key in ['short_exit_bid', 'short_exit_ask',
                    'long_exit_bid', 'long_exit_ask',
                    'underlying_exit_price', 'underlying_change_pct',
                    'stop_threshold', 'actual_value',
                    'call_iv_exit', 'put_iv_exit', 'iv_lean_exit',
                    'spy_intraday_high', 'spy_intraday_low', 'spy_intraday_close',
                    'spy_stop_trigger_time', 'spy_stop_trigger_price',
                    'spy_stop_trigger_bid', 'spy_stop_trigger_ask', 'spy_stop_trigger_last',
                    'intraday_data_points', 'intraday_data_available', 'stop_triggered_by']:
            if key in kwargs:
                trade[key] = kwargs[key]
        
        self.closed_trades.append(trade)
        
        if self.sl_enabled and self.sl_manager:
            self.sl_manager.remove_position(position_id)
        
        if self.debug:
            print(f"[PositionManager] CLOSE {position_id}: P&L=${pnl:.2f} ({pnl_pct:.2f}%) - {close_reason}")
        
        return trade
            
    def get_open_positions(self):
        return list(self.positions.values())
    
    def get_closed_trades(self):
        return self.closed_trades
    
    def close_all_positions(self, final_date, price_data, reason='end_of_backtest'):
        """Close all open positions at end of backtest"""
        for position_id in list(self.positions.keys()):
            if position_id in price_data:
                position = self.positions[position_id]
                
                if isinstance(price_data[position_id], dict):
                    data = price_data[position_id]
                    exit_price = data.get('price', position['entry_price'])
                    pnl = data.get('pnl', None)
                else:
                    exit_price = price_data[position_id]
                    pnl = None
                
                if pnl is None and position['entry_price'] == 0:
                    if isinstance(price_data[position_id], dict) and 'pnl' in price_data[position_id]:
                        pnl = price_data[position_id]['pnl']
                
                self.close_position(
                    position_id=position_id,
                    exit_date=final_date,
                    exit_price=exit_price,
                    close_reason=reason,
                    pnl=pnl
                )


# ============================================================
# BACKTEST ANALYZER (unchanged)
# ============================================================
class BacktestAnalyzer:
    """Calculate all metrics from BacktestResults"""
    
    def __init__(self, results):
        self.results = results
        self.metrics = {}
    
    def calculate_all_metrics(self):
        r = self.results
        
        self.metrics['initial_capital'] = r.initial_capital
        self.metrics['final_equity'] = r.final_capital
        
        self.metrics['total_pnl'] = r.final_capital - r.initial_capital
        self.metrics['total_return'] = (self.metrics['total_pnl'] / r.initial_capital) * 100
        
        if len(r.equity_dates) > 0:
            start_date = min(r.equity_dates)
            end_date = max(r.equity_dates)
            days_diff = (end_date - start_date).days
            
            if days_diff <= 0:
                self.metrics['cagr'] = 0
                self.metrics['show_cagr'] = False
            else:
                years = days_diff / 365.25
                if years >= 1.0:
                    self.metrics['cagr'] = ((r.final_capital / r.initial_capital) ** (1/years) - 1) * 100
                    self.metrics['show_cagr'] = True
                else:
                    self.metrics['cagr'] = self.metrics['total_return'] * (365.25 / days_diff)
                    self.metrics['show_cagr'] = False
        else:
            self.metrics['cagr'] = 0
            self.metrics['show_cagr'] = False
        
        self.metrics['sharpe'] = self._sharpe_ratio(r.daily_returns)
        self.metrics['sortino'] = self._sortino_ratio(r.daily_returns)
        self.metrics['max_drawdown'] = r.max_drawdown
        self.metrics['volatility'] = np.std(r.daily_returns) * np.sqrt(252) * 100 if len(r.daily_returns) > 0 else 0
        self.metrics['calmar'] = abs(self.metrics['total_return'] / r.max_drawdown) if r.max_drawdown > 0 else 0
        self.metrics['omega'] = self._omega_ratio(r.daily_returns)
        self.metrics['ulcer'] = self._ulcer_index(r.equity_curve)
        
        self.metrics['var_95'], self.metrics['var_95_pct'] = self._calculate_var(r.daily_returns, 0.95)
        self.metrics['var_99'], self.metrics['var_99_pct'] = self._calculate_var(r.daily_returns, 0.99)
        self.metrics['cvar_95'], self.metrics['cvar_95_pct'] = self._calculate_cvar(r.daily_returns, 0.95)
        
        avg_equity = np.mean(r.equity_curve) if len(r.equity_curve) > 0 else r.initial_capital
        self.metrics['var_95_dollar'] = self.metrics['var_95'] * avg_equity
        self.metrics['var_99_dollar'] = self.metrics['var_99'] * avg_equity
        self.metrics['cvar_95_dollar'] = self.metrics['cvar_95'] * avg_equity
        
        self.metrics['tail_ratio'] = self._tail_ratio(r.daily_returns)
        self.metrics['skewness'], self.metrics['kurtosis'] = self._skewness_kurtosis(r.daily_returns)
        
        self.metrics['alpha'], self.metrics['beta'], self.metrics['r_squared'] = self._alpha_beta(r)
        
        if len(r.trades) > 0:
            self._calculate_trading_stats(r.trades)
        else:
            self._set_empty_trading_stats()
        
        running_max = np.maximum.accumulate(r.equity_curve)
        max_dd_dollars = np.min(np.array(r.equity_curve) - running_max)
        self.metrics['recovery_factor'] = self.metrics['total_pnl'] / abs(max_dd_dollars) if max_dd_dollars != 0 else 0
        
        if len(r.trades) > 0 and 'start_date' in r.config and 'end_date' in r.config:
            total_days = (pd.to_datetime(r.config['end_date']) - pd.to_datetime(r.config['start_date'])).days
            self.metrics['exposure_time'] = self._exposure_time(r.trades, total_days)
        else:
            self.metrics['exposure_time'] = 0
        
        return self.metrics
    
    def _calculate_trading_stats(self, trades):
        trades_df = pd.DataFrame(trades)
        winning = trades_df[trades_df['pnl'] > 0]
        losing = trades_df[trades_df['pnl'] <= 0]
        
        self.metrics['total_trades'] = len(trades_df)
        self.metrics['winning_trades'] = len(winning)
        self.metrics['losing_trades'] = len(losing)
        self.metrics['win_rate'] = (len(winning) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
        
        wins_sum = winning['pnl'].sum() if len(winning) > 0 else 0
        losses_sum = abs(losing['pnl'].sum()) if len(losing) > 0 else 0
        self.metrics['profit_factor'] = wins_sum / losses_sum if losses_sum > 0 else float('inf')
        
        self.metrics['avg_win'] = winning['pnl'].mean() if len(winning) > 0 else 0
        self.metrics['avg_loss'] = losing['pnl'].mean() if len(losing) > 0 else 0
        self.metrics['best_trade'] = trades_df['pnl'].max()
        self.metrics['worst_trade'] = trades_df['pnl'].min()
        
        if len(winning) > 0 and len(losing) > 0:
            self.metrics['avg_win_loss_ratio'] = abs(self.metrics['avg_win'] / self.metrics['avg_loss'])
        else:
            self.metrics['avg_win_loss_ratio'] = 0
        
        self.metrics['max_win_streak'], self.metrics['max_loss_streak'] = self._win_loss_streaks(trades)
    
    def _set_empty_trading_stats(self):
        self.metrics.update({
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
            'win_rate': 0, 'profit_factor': 0, 'avg_win': 0, 'avg_loss': 0,
            'best_trade': 0, 'worst_trade': 0, 'avg_win_loss_ratio': 0,
            'max_win_streak': 0, 'max_loss_streak': 0
        })
    
    def _sharpe_ratio(self, returns):
        if len(returns) < 2:
            return 0
        return np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
    
    def _sortino_ratio(self, returns):
        if len(returns) < 2:
            return 0
        returns_array = np.array(returns)
        downside = returns_array[returns_array < 0]
        if len(downside) == 0 or np.std(downside) == 0:
            return 0
        return np.sqrt(252) * np.mean(returns_array) / np.std(downside)
    
    def _omega_ratio(self, returns, threshold=0):
        if len(returns) < 2:
            return 0
        returns_array = np.array(returns)
        gains = np.sum(np.maximum(returns_array - threshold, 0))
        losses = np.sum(np.maximum(threshold - returns_array, 0))
        return gains / losses if losses > 0 else float('inf')
    
    def _ulcer_index(self, equity_curve):
        if len(equity_curve) < 2:
            return 0
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        return np.sqrt(np.mean(drawdown ** 2)) * 100
    
    def _calculate_var(self, returns, confidence=0.95):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        returns_array = returns_array[~np.isnan(returns_array)]
        if len(returns_array) < 10:
            return 0, 0
        var_percentile = (1 - confidence) * 100
        var_return = np.percentile(returns_array, var_percentile)
        return var_return, var_return * 100
    
    def _calculate_cvar(self, returns, confidence=0.95):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        returns_array = returns_array[~np.isnan(returns_array)]
        if len(returns_array) < 10:
            return 0, 0
        var_percentile = (1 - confidence) * 100
        var_threshold = np.percentile(returns_array, var_percentile)
        tail_losses = returns_array[returns_array <= var_threshold]
        if len(tail_losses) == 0:
            return 0, 0
        cvar_return = np.mean(tail_losses)
        return cvar_return, cvar_return * 100
    
    def _tail_ratio(self, returns):
        if len(returns) < 20:
            return 0
        returns_array = np.array(returns)
        right = np.percentile(returns_array, 95)
        left = abs(np.percentile(returns_array, 5))
        return right / left if left > 0 else 0
    
    def _skewness_kurtosis(self, returns):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        mean = np.mean(returns_array)
        std = np.std(returns_array)
        if std == 0:
            return 0, 0
        skew = np.mean(((returns_array - mean) / std) ** 3)
        kurt = np.mean(((returns_array - mean) / std) ** 4) - 3
        return skew, kurt
    
    def _alpha_beta(self, results):
        if not hasattr(results, 'benchmark_prices') or not results.benchmark_prices:
            return 0, 0, 0
        if len(results.equity_dates) < 10:
            return 0, 0, 0
        
        benchmark_returns = []
        sorted_dates = sorted(results.equity_dates)
        
        for i in range(1, len(sorted_dates)):
            prev_date = sorted_dates[i-1]
            curr_date = sorted_dates[i]
            
            if prev_date in results.benchmark_prices and curr_date in results.benchmark_prices:
                prev_price = results.benchmark_prices[prev_date]
                curr_price = results.benchmark_prices[curr_date]
                bench_return = (curr_price - prev_price) / prev_price
                benchmark_returns.append(bench_return)
            else:
                benchmark_returns.append(0)
        
        if len(benchmark_returns) != len(results.daily_returns):
            return 0, 0, 0
        
        port_ret = np.array(results.daily_returns)
        bench_ret = np.array(benchmark_returns)
        
        bench_mean = np.mean(bench_ret)
        port_mean = np.mean(port_ret)
        
        covariance = np.mean((bench_ret - bench_mean) * (port_ret - port_mean))
        benchmark_variance = np.mean((bench_ret - bench_mean) ** 2)
        
        if benchmark_variance == 0:
            return 0, 0, 0
        
        beta = covariance / benchmark_variance
        alpha_daily = port_mean - beta * bench_mean
        alpha_annualized = alpha_daily * 252 * 100
        
        ss_res = np.sum((port_ret - (alpha_daily + beta * bench_ret)) ** 2)
        ss_tot = np.sum((port_ret - port_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return alpha_annualized, beta, r_squared
    
    def _win_loss_streaks(self, trades):
        if len(trades) == 0:
            return 0, 0
        max_win = max_loss = current_win = current_loss = 0
        for trade in trades:
            if trade['pnl'] > 0:
                current_win += 1
                current_loss = 0
                max_win = max(max_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                max_loss = max(max_loss, current_loss)
        return max_win, max_loss
    
    def _exposure_time(self, trades, total_days):
        if total_days <= 0 or len(trades) == 0:
            return 0
        days_with_positions = set()
        for trade in trades:
            entry = pd.to_datetime(trade['entry_date'])
            exit_ = pd.to_datetime(trade['exit_date'])
            date_range = pd.date_range(start=entry, end=exit_, freq='D')
            days_with_positions.update(date_range.date)
        exposure_pct = (len(days_with_positions) / total_days) * 100
        return min(exposure_pct, 100.0)


# ============================================================
# STOP-LOSS METRICS (unchanged)
# ============================================================
def calculate_stoploss_metrics(analyzer):
    """Calculate stop-loss specific metrics"""
    if len(analyzer.results.trades) == 0:
        _set_empty_stoploss_metrics(analyzer)
        return analyzer.metrics
    
    trades_df = pd.DataFrame(analyzer.results.trades)
    
    if 'exit_reason' not in trades_df.columns:
        _set_empty_stoploss_metrics(analyzer)
        return analyzer.metrics
    
    sl_trades = trades_df[trades_df['exit_reason'].str.contains('stop_loss', na=False)]
    profit_target_trades = trades_df[trades_df['exit_reason'] == 'profit_target']
    
    analyzer.metrics['stoploss_count'] = len(sl_trades)
    analyzer.metrics['stoploss_pct'] = (len(sl_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    analyzer.metrics['profit_target_count'] = len(profit_target_trades)
    analyzer.metrics['profit_target_pct'] = (len(profit_target_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    
    if len(sl_trades) > 0:
        analyzer.metrics['avg_stoploss_pnl'] = sl_trades['pnl'].mean()
        analyzer.metrics['total_stoploss_loss'] = sl_trades['pnl'].sum()
        analyzer.metrics['worst_stoploss'] = sl_trades['pnl'].min()
        
        if 'return_pct' in sl_trades.columns:
            analyzer.metrics['avg_stoploss_return_pct'] = sl_trades['return_pct'].mean()
        else:
            analyzer.metrics['avg_stoploss_return_pct'] = 0
        
        if 'entry_date' in sl_trades.columns and 'exit_date' in sl_trades.columns:
            sl_trades_copy = sl_trades.copy()
            sl_trades_copy['entry_date'] = pd.to_datetime(sl_trades_copy['entry_date'])
            sl_trades_copy['exit_date'] = pd.to_datetime(sl_trades_copy['exit_date'])
            sl_trades_copy['days_held'] = (sl_trades_copy['exit_date'] - sl_trades_copy['entry_date']).dt.days
            analyzer.metrics['avg_days_to_stoploss'] = sl_trades_copy['days_held'].mean()
            analyzer.metrics['min_days_to_stoploss'] = sl_trades_copy['days_held'].min()
            analyzer.metrics['max_days_to_stoploss'] = sl_trades_copy['days_held'].max()
        else:
            analyzer.metrics['avg_days_to_stoploss'] = 0
            analyzer.metrics['min_days_to_stoploss'] = 0
            analyzer.metrics['max_days_to_stoploss'] = 0
        
        if 'stop_type' in sl_trades.columns:
            stop_types = sl_trades['stop_type'].value_counts().to_dict()
            analyzer.metrics['stoploss_by_type'] = stop_types
        else:
            analyzer.metrics['stoploss_by_type'] = {}
    else:
        analyzer.metrics['avg_stoploss_pnl'] = 0
        analyzer.metrics['total_stoploss_loss'] = 0
        analyzer.metrics['worst_stoploss'] = 0
        analyzer.metrics['avg_stoploss_return_pct'] = 0
        analyzer.metrics['avg_days_to_stoploss'] = 0
        analyzer.metrics['min_days_to_stoploss'] = 0
        analyzer.metrics['max_days_to_stoploss'] = 0
        analyzer.metrics['stoploss_by_type'] = {}
    
    if len(profit_target_trades) > 0 and len(sl_trades) > 0:
        avg_profit_target = profit_target_trades['pnl'].mean()
        avg_stoploss = abs(sl_trades['pnl'].mean())
        analyzer.metrics['profit_to_loss_ratio'] = avg_profit_target / avg_stoploss if avg_stoploss > 0 else 0
    else:
        analyzer.metrics['profit_to_loss_ratio'] = 0
    
    if 'max_profit_before_stop' in sl_trades.columns:
        early_exits = sl_trades[sl_trades['max_profit_before_stop'] > 0]
        analyzer.metrics['early_exit_count'] = len(early_exits)
        analyzer.metrics['early_exit_pct'] = (len(early_exits) / len(sl_trades)) * 100 if len(sl_trades) > 0 else 0
        if len(early_exits) > 0:
            analyzer.metrics['avg_missed_profit'] = early_exits['max_profit_before_stop'].mean()
        else:
            analyzer.metrics['avg_missed_profit'] = 0
    else:
        analyzer.metrics['early_exit_count'] = 0
        analyzer.metrics['early_exit_pct'] = 0
        analyzer.metrics['avg_missed_profit'] = 0
    
    exit_reasons = trades_df['exit_reason'].value_counts().to_dict()
    analyzer.metrics['exit_reasons'] = exit_reasons
    
    return analyzer.metrics


def _set_empty_stoploss_metrics(analyzer):
    analyzer.metrics.update({
        'stoploss_count': 0, 'stoploss_pct': 0,
        'profit_target_count': 0, 'profit_target_pct': 0,
        'avg_stoploss_pnl': 0, 'total_stoploss_loss': 0,
        'worst_stoploss': 0, 'avg_stoploss_return_pct': 0,
        'avg_days_to_stoploss': 0, 'min_days_to_stoploss': 0,
        'max_days_to_stoploss': 0, 'stoploss_by_type': {},
        'profit_to_loss_ratio': 0, 'early_exit_count': 0,
        'early_exit_pct': 0, 'avg_missed_profit': 0,
        'exit_reasons': {}
    })


# ============================================================
# RESULTS REPORTER (unchanged)
# ============================================================
class ResultsReporter:
    """Print comprehensive metrics report"""
    
    @staticmethod
    def print_full_report(analyzer):
        m = analyzer.metrics
        r = analyzer.results
        
        print("="*80)
        print(" "*25 + "BACKTEST RESULTS")
        print("="*80)
        print()
        
        print("PROFITABILITY METRICS")
        print("-"*80)
        print(f"Initial Capital:        ${r.initial_capital:>15,.2f}")
        print(f"Final Equity:           ${r.final_capital:>15,.2f}")
        print(f"Total P&L:              ${m['total_pnl']:>15,.2f}  (absolute profit/loss)")
        print(f"Total Return:            {m['total_return']:>15.2f}%  (% gain/loss)")
        if m['cagr'] != 0:
            if m['show_cagr']:
                print(f"CAGR:                    {m['cagr']:>15.2f}%  (annualized compound growth)")
            else:
                print(f"Annualized Return:       {m['cagr']:>15.2f}%  (extrapolated to 1 year)")
        print()
        
        print("RISK METRICS")
        print("-"*80)
        print(f"Sharpe Ratio:            {m['sharpe']:>15.2f}  (>1 good, >2 excellent)")
        print(f"Sortino Ratio:           {m['sortino']:>15.2f}  (downside risk, >2 good)")
        print(f"Calmar Ratio:            {m['calmar']:>15.2f}  (return/drawdown, >3 good)")
        if m['omega'] != 0:
            omega_display = f"{m['omega']:.2f}" if m['omega'] < 999 else "∞"
            print(f"Omega Ratio:             {omega_display:>15s}  (gains/losses, >1 good)")
        print(f"Maximum Drawdown:        {m['max_drawdown']:>15.2f}%  (peak to trough)")
        if m['ulcer'] != 0:
            print(f"Ulcer Index:             {m['ulcer']:>15.2f}%  (pain of drawdowns, lower better)")
        print(f"Volatility (ann.):       {m['volatility']:>15.2f}%  (annualized std dev)")
        
        if len(r.daily_returns) >= 10:
            print(f"VaR (95%, 1-day):        {m['var_95_pct']:>15.2f}% (${m['var_95_dollar']:>,.0f})  (max loss 95% confidence)")
            print(f"VaR (99%, 1-day):        {m['var_99_pct']:>15.2f}% (${m['var_99_dollar']:>,.0f})  (max loss 99% confidence)")
            print(f"CVaR (95%, 1-day):       {m['cvar_95_pct']:>15.2f}% (${m['cvar_95_dollar']:>,.0f})  (avg loss in worst 5%)")
        
        if m['tail_ratio'] != 0:
            print(f"Tail Ratio (95/5):       {m['tail_ratio']:>15.2f}  (big wins/losses, >1 good)")
        
        if m['skewness'] != 0 or m['kurtosis'] != 0:
            print(f"Skewness:                {m['skewness']:>15.2f}  (>0 positive tail)")
            print(f"Kurtosis (excess):       {m['kurtosis']:>15.2f}  (>0 fat tails)")
        
        if m['beta'] != 0 or m['alpha'] != 0:
            print(f"Alpha (vs {r.benchmark_symbol}):     {m['alpha']:>15.2f}%  (excess return)")
            print(f"Beta (vs {r.benchmark_symbol}):      {m['beta']:>15.2f}  (<1 defensive, >1 aggressive)")
            print(f"R² (vs {r.benchmark_symbol}):        {m['r_squared']:>15.2f}  (market correlation 0-1)")
        
        if abs(m['total_return']) > 200 or m['volatility'] > 150:
            print()
            print("WARNING: UNREALISTIC RESULTS DETECTED")
            if abs(m['total_return']) > 200:
                print(f"  Total return {m['total_return']:.1f}% is extremely high")
            if m['volatility'] > 150:
                print(f"  Volatility {m['volatility']:.1f}% is higher than leveraged ETFs")
            print("  Review configuration before trusting results")
        
        print()
        
        print("EFFICIENCY METRICS")
        print("-"*80)
        if m['recovery_factor'] != 0:
            print(f"Recovery Factor:         {m['recovery_factor']:>15.2f}  (profit/max DD, >3 good)")
        if m['exposure_time'] != 0:
            print(f"Exposure Time:           {m['exposure_time']:>15.1f}%  (time in market)")
        print()
        
        print("TRADING STATISTICS")
        print("-"*80)
        print(f"Total Trades:            {m['total_trades']:>15}")
        print(f"Winning Trades:          {m['winning_trades']:>15}")
        print(f"Losing Trades:           {m['losing_trades']:>15}")
        print(f"Win Rate:                {m['win_rate']:>15.2f}%  (% profitable trades)")
        print(f"Profit Factor:           {m['profit_factor']:>15.2f}  (gross profit/loss, >1.5 good)")
        if m['max_win_streak'] > 0 or m['max_loss_streak'] > 0:
            print(f"Max Win Streak:          {m['max_win_streak']:>15}  (consecutive wins)")
            print(f"Max Loss Streak:         {m['max_loss_streak']:>15}  (consecutive losses)")
        print(f"Average Win:            ${m['avg_win']:>15,.2f}")
        print(f"Average Loss:           ${m['avg_loss']:>15,.2f}")
        print(f"Best Trade:             ${m['best_trade']:>15,.2f}")
        print(f"Worst Trade:            ${m['worst_trade']:>15,.2f}")
        if m['avg_win_loss_ratio'] != 0:
            print(f"Avg Win/Loss Ratio:      {m['avg_win_loss_ratio']:>15.2f}  (avg win / avg loss)")
        print()
        print("="*80)


def print_stoploss_section(analyzer):
    """Print stop-loss analysis section"""
    m = analyzer.metrics
    
    if m.get('stoploss_count', 0) == 0:
        return
    
    print("STOP-LOSS ANALYSIS")
    print("-"*80)
    
    print(f"Stop-Loss Trades:        {m['stoploss_count']:>15}  ({m['stoploss_pct']:.1f}% of total)")
    print(f"Profit Target Trades:    {m['profit_target_count']:>15}  ({m['profit_target_pct']:.1f}% of total)")
    
    print(f"Avg Stop-Loss P&L:      ${m['avg_stoploss_pnl']:>15,.2f}")
    print(f"Total Loss from SL:     ${m['total_stoploss_loss']:>15,.2f}")
    print(f"Worst Stop-Loss:        ${m['worst_stoploss']:>15,.2f}")
    print(f"Avg SL Return:           {m['avg_stoploss_return_pct']:>15.2f}%")
    
    if m['avg_days_to_stoploss'] > 0:
        print(f"Avg Days to SL:          {m['avg_days_to_stoploss']:>15.1f}")
        print(f"Min/Max Days to SL:      {m['min_days_to_stoploss']:>7} / {m['max_days_to_stoploss']:<7}")
    
    if m['profit_to_loss_ratio'] > 0:
        print(f"Profit/Loss Ratio:       {m['profit_to_loss_ratio']:>15.2f}  (avg profit target / avg stop-loss)")
    
    if m['early_exit_count'] > 0:
        print(f"Early Exits:             {m['early_exit_count']:>15}  ({m['early_exit_pct']:.1f}% of SL trades)")
        print(f"Avg Missed Profit:      ${m['avg_missed_profit']:>15,.2f}  (profit before stop triggered)")
    
    if m['stoploss_by_type']:
        print(f"\nStop-Loss Types:")
        for stop_type, count in m['stoploss_by_type'].items():
            pct = (count / m['stoploss_count']) * 100
            print(f"  {stop_type:20s} {count:>5} trades ({pct:.1f}%)")
    
    if m.get('exit_reasons'):
        print(f"\nExit Reasons Distribution:")
        total_trades = sum(m['exit_reasons'].values())
        for reason, count in sorted(m['exit_reasons'].items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_trades) * 100
            print(f"  {reason:20s} {count:>5} trades ({pct:.1f}%)")
    
    print()
    print("="*80)


# ============================================================
# CHART GENERATOR (only core charts, optimization charts separate)
# ============================================================
class ChartGenerator:
    """Generate 6 professional charts"""
    
    @staticmethod
    def create_all_charts(analyzer, filename='backtest_results.png', show_plots=True):
        r = analyzer.results
        
        if len(r.trades) == 0:
            print("No trades to visualize")
            return
        
        trades_df = pd.DataFrame(r.trades)
        fig, axes = plt.subplots(3, 2, figsize=(18, 14))
        fig.suptitle('Backtest Results', fontsize=16, fontweight='bold', y=0.995)
        
        dates = pd.to_datetime(r.equity_dates)
        equity_array = np.array(r.equity_curve)
        
        ax1 = axes[0, 0]
        ax1.plot(dates, equity_array, linewidth=2.5, color='#2196F3')
        ax1.axhline(y=r.initial_capital, color='gray', linestyle='--', alpha=0.7)
        ax1.fill_between(dates, r.initial_capital, equity_array,
                         where=(equity_array >= r.initial_capital), 
                         alpha=0.3, color='green', interpolate=True)
        ax1.fill_between(dates, r.initial_capital, equity_array,
                         where=(equity_array < r.initial_capital), 
                         alpha=0.3, color='red', interpolate=True)
        ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Equity ($)')
        ax1.grid(True, alpha=0.3)
        
        ax2 = axes[0, 1]
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        ax2.fill_between(dates, 0, drawdown, alpha=0.6, color='#f44336')
        ax2.plot(dates, drawdown, color='#d32f2f', linewidth=2)
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        
        ax3 = axes[1, 0]
        pnl_values = trades_df['pnl'].values
        ax3.hist(pnl_values, bins=40, color='#4CAF50', alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax3.set_title('P&L Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('P&L ($)')
        ax3.grid(True, alpha=0.3, axis='y')
        
        ax4 = axes[1, 1]
        if 'signal' in trades_df.columns:
            signal_pnl = trades_df.groupby('signal')['pnl'].sum()
            colors = ['#4CAF50' if x > 0 else '#f44336' for x in signal_pnl.values]
            ax4.bar(signal_pnl.index, signal_pnl.values, color=colors, alpha=0.7)
            ax4.set_title('P&L by Signal', fontsize=12, fontweight='bold')
        else:
            ax4.text(0.5, 0.5, 'No signal data', ha='center', va='center', transform=ax4.transAxes)
        ax4.axhline(y=0, color='black', linewidth=1)
        ax4.grid(True, alpha=0.3, axis='y')
        
        ax5 = axes[2, 0]
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        trades_df['month'] = trades_df['exit_date'].dt.to_period('M')
        monthly_pnl = trades_df.groupby('month')['pnl'].sum()
        colors = ['#4CAF50' if x > 0 else '#f44336' for x in monthly_pnl.values]
        ax5.bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7)
        ax5.set_title('Monthly P&L', fontsize=12, fontweight='bold')
        ax5.set_xticks(range(len(monthly_pnl)))
        ax5.set_xticklabels([str(m) for m in monthly_pnl.index], rotation=45, ha='right')
        ax5.axhline(y=0, color='black', linewidth=1)
        ax5.grid(True, alpha=0.3, axis='y')
        
        ax6 = axes[2, 1]
        if 'symbol' in trades_df.columns:
            symbol_pnl = trades_df.groupby('symbol')['pnl'].sum().sort_values(ascending=True).tail(10)
            colors = ['#4CAF50' if x > 0 else '#f44336' for x in symbol_pnl.values]
            ax6.barh(range(len(symbol_pnl)), symbol_pnl.values, color=colors, alpha=0.7)
            ax6.set_yticks(range(len(symbol_pnl)))
            ax6.set_yticklabels(symbol_pnl.index, fontsize=9)
            ax6.set_title('Top Symbols', fontsize=12, fontweight='bold')
        else:
            ax6.text(0.5, 0.5, 'No symbol data', ha='center', va='center', transform=ax6.transAxes)
        ax6.axvline(x=0, color='black', linewidth=1)
        ax6.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        if show_plots:
            plt.show()
        else:
            plt.close()  # Закрываем без показа
        
        print(f"Chart saved: {filename}")


def create_stoploss_charts(analyzer, filename='stoploss_analysis.png', show_plots=True):
    """Create 4 stop-loss specific charts"""
    r = analyzer.results
    m = analyzer.metrics
    
    if m.get('stoploss_count', 0) == 0:
        print("No stop-loss trades to visualize")
        return
    
    trades_df = pd.DataFrame(r.trades)
    
    if 'exit_reason' not in trades_df.columns:
        print("No exit_reason data available")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Stop-Loss Analysis', fontsize=16, fontweight='bold', y=0.995)
    
    ax1 = axes[0, 0]
    if m.get('exit_reasons'):
        reasons = pd.Series(m['exit_reasons']).sort_values(ascending=True)
        colors = ['#f44336' if 'stop_loss' in str(r) else '#4CAF50' if r == 'profit_target' else '#2196F3' 
                  for r in reasons.index]
        ax1.barh(range(len(reasons)), reasons.values, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_yticks(range(len(reasons)))
        ax1.set_yticklabels([r.replace('_', ' ').title() for r in reasons.index])
        ax1.set_title('Exit Reasons Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Number of Trades')
        ax1.grid(True, alpha=0.3, axis='x')
        
        total = sum(reasons.values)
        for i, v in enumerate(reasons.values):
            ax1.text(v, i, f' {(v/total)*100:.1f}%', va='center', fontweight='bold')
    
    ax2 = axes[0, 1]
    sl_trades = trades_df[trades_df['exit_reason'].str.contains('stop_loss', na=False)]
    if len(sl_trades) > 0:
        ax2.hist(sl_trades['pnl'], bins=30, color='#f44336', alpha=0.7, edgecolor='black')
        ax2.axvline(x=0, color='black', linestyle='--', linewidth=2)
        ax2.axvline(x=sl_trades['pnl'].mean(), color='yellow', linestyle='--', linewidth=2, label='Mean')
        ax2.set_title('Stop-Loss P&L Distribution', fontsize=12, fontweight='bold')
        ax2.set_xlabel('P&L ($)')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
    
    ax3 = axes[1, 0]
    if len(sl_trades) > 0 and 'entry_date' in sl_trades.columns and 'exit_date' in sl_trades.columns:
        sl_trades_copy = sl_trades.copy()
        sl_trades_copy['entry_date'] = pd.to_datetime(sl_trades_copy['entry_date'])
        sl_trades_copy['exit_date'] = pd.to_datetime(sl_trades_copy['exit_date'])
        sl_trades_copy['days_held'] = (sl_trades_copy['exit_date'] - sl_trades_copy['entry_date']).dt.days
        
        ax3.hist(sl_trades_copy['days_held'], bins=30, color='#FF9800', alpha=0.7, edgecolor='black')
        ax3.axvline(x=sl_trades_copy['days_held'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
        ax3.set_title('Days Until Stop-Loss Triggered', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Days Held')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
    
    ax4 = axes[1, 1]
    if 'stop_type' in sl_trades.columns:
        stop_types = sl_trades['stop_type'].value_counts()
        colors_types = plt.cm.Set3(range(len(stop_types)))
        wedges, texts, autotexts = ax4.pie(stop_types.values, labels=stop_types.index, 
                                            autopct='%1.1f%%', colors=colors_types,
                                            startangle=90)
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        ax4.set_title('Stop-Loss Types', fontsize=12, fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No stop_type data', ha='center', va='center', transform=ax4.transAxes)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    print(f"Stop-loss charts saved: {filename}")


# ============================================================
# RESULTS EXPORTER (unchanged)
# ============================================================
class ResultsExporter:
    """Export results to CSV"""
    
    @staticmethod
    def export_all(analyzer, prefix='backtest'):
        r = analyzer.results
        m = analyzer.metrics
        
        if len(r.trades) == 0:
            print("No trades to export")
            return
        
        trades_df = pd.DataFrame(r.trades)
        
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.strftime('%Y-%m-%d')
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.strftime('%Y-%m-%d')
        
        # Round numeric columns to 5 decimal places
        numeric_columns = trades_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            trades_df[col] = trades_df[col].round(5)
        
        core_columns = [
            'entry_date', 'exit_date', 'symbol', 'signal',
            'pnl', 'return_pct', 'exit_reason', 'stop_type'
        ]
        
        options_columns = [
            'short_strike', 'long_strike', 'expiration', 'opt_type', 
            'spread_type', 'contracts'
        ]
        
        bidask_columns = [
            'short_entry_bid', 'short_entry_ask', 'short_entry_mid',
            'long_entry_bid', 'long_entry_ask', 'long_entry_mid',
            'short_exit_bid', 'short_exit_ask',
            'long_exit_bid', 'long_exit_ask'
        ]
        
        underlying_columns = [
            'underlying_entry_price', 'underlying_exit_price', 
            'underlying_change_pct'
        ]
        
        stop_columns = [
            'stop_threshold', 'actual_value'
        ]
        
        strategy_columns = [
            'entry_z_score', 'is_short_bias', 'entry_price', 
            'exit_price', 'quantity', 'entry_lean', 'exit_lean',
            # IV EOD fields
            'call_iv_entry', 'put_iv_entry', 'call_iv_exit', 'put_iv_exit',
            'iv_lean_entry', 'iv_lean_exit'
        ]
        
        # NEW: Intraday stop-loss columns
        intraday_columns = [
            'spy_intraday_high', 'spy_intraday_low', 'spy_intraday_close',
            'spy_stop_trigger_time', 'spy_stop_trigger_price', 
            'spy_stop_trigger_bid', 'spy_stop_trigger_ask', 'spy_stop_trigger_last',
            'intraday_data_points', 'intraday_data_available', 'stop_triggered_by'
        ]
        
        ordered_columns = []
        for col in (core_columns + options_columns + bidask_columns + 
                    underlying_columns + stop_columns + strategy_columns + intraday_columns):
            if col in trades_df.columns:
                ordered_columns.append(col)
        
        remaining = [col for col in trades_df.columns if col not in ordered_columns]
        ordered_columns.extend(remaining)
        
        trades_df = trades_df[ordered_columns]
        
        # Round numeric columns to 2 decimals
        numeric_columns = trades_df.select_dtypes(include=['float64', 'float32', 'float']).columns
        for col in numeric_columns:
            trades_df[col] = trades_df[col].round(5)
        
        trades_df.to_csv(f'{prefix}_trades.csv', index=False)
        print(f"Exported: {prefix}_trades.csv ({len(ordered_columns)} columns)")
        
        equity_df = pd.DataFrame({
            'date': pd.to_datetime(r.equity_dates).strftime('%Y-%m-%d'),
            'equity': r.equity_curve
        })
        equity_df['equity'] = equity_df['equity'].round(5)
        equity_df.to_csv(f'{prefix}_equity.csv', index=False)
        print(f"Exported: {prefix}_equity.csv")
        
        with open(f'{prefix}_summary.txt', 'w') as f:
            f.write("BACKTEST SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Strategy: {r.config.get('strategy_name', 'Unknown')}\n")
            f.write(f"Period: {r.config.get('start_date')} to {r.config.get('end_date')}\n\n")
            f.write("PERFORMANCE\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Return: {m['total_return']:.2f}%\n")
            f.write(f"Sharpe: {m['sharpe']:.2f}\n")
            f.write(f"Max DD: {m['max_drawdown']:.2f}%\n")
            f.write(f"Trades: {m['total_trades']}\n")
        
        print(f"Exported: {prefix}_summary.txt")
        
        # Export metrics as JSON with rounded values
        import json
        metrics_rounded = {}
        for key, value in m.items():
            if isinstance(value, (int, float)):
                metrics_rounded[key] = round(float(value), 5) if isinstance(value, float) else value
            else:
                metrics_rounded[key] = value
        
        with open(f'{prefix}_metrics.json', 'w') as f:
            json.dump(metrics_rounded, f, indent=2)
        
        print(f"Exported: {prefix}_metrics.json")


# ============================================================
# RUN BACKTEST (unchanged)
# ============================================================
def run_backtest(strategy_function, config, print_report=True,
                 create_charts=True, export_results=True,
                 chart_filename='backtest_results.png',
                 export_prefix='backtest',
                 progress_context=None):
    """Run complete backtest"""
    
    # Check if running inside optimization
    is_optimization = progress_context and progress_context.get('is_optimization', False)
    
    if not progress_context and not is_optimization:
        print("="*80)
        print(" "*25 + "STARTING BACKTEST")
        print("="*80)
        print(f"Strategy: {config.get('strategy_name', 'Unknown')}")
        print(f"Period: {config.get('start_date')} to {config.get('end_date')}")
        print(f"Capital: ${config.get('initial_capital', 0):,.0f}")
        print("="*80 + "\n")
    
    if progress_context:
        config['_progress_context'] = progress_context
    
    results = strategy_function(config)
    
    if '_progress_context' in config:
        del config['_progress_context']
    
    if not is_optimization:
        print("\n[*] Calculating metrics...")
    analyzer = BacktestAnalyzer(results)
    analyzer.calculate_all_metrics()
    
    if print_report:
        print("\n" + "="*80)
        ResultsReporter.print_full_report(analyzer)
    
    # Export charts during optimization if requested
    if create_charts and len(results.trades) > 0:
        if not is_optimization:
            print(f"\n[*] Creating charts: {chart_filename}")
        try:
            # Don't show plots during optimization, just save them
            ChartGenerator.create_all_charts(analyzer, chart_filename, show_plots=not is_optimization)
        except Exception as e:
            if not is_optimization:
                print(f"[ERROR] Charts failed: {e}")
    
    # Export results during optimization if requested
    if export_results and len(results.trades) > 0:
        if not is_optimization:
            print(f"\n[*] Exporting: {export_prefix}_*")
        try:
            ResultsExporter.export_all(analyzer, export_prefix)
        except Exception as e:
            if not is_optimization:
                print(f"[ERROR] Export failed: {e}")
    
    return analyzer


def run_backtest_with_stoploss(strategy_function, config, print_report=True,
                               create_charts=True, export_results=True,
                               chart_filename='backtest_results.png',
                               export_prefix='backtest',
                               create_stoploss_report=True,
                               create_stoploss_charts=True,
                               progress_context=None):
    """Enhanced run_backtest with stop-loss analysis"""
    
    analyzer = run_backtest(
        strategy_function, config,
        print_report=False,
        create_charts=create_charts,
        export_results=export_results,
        chart_filename=chart_filename,
        export_prefix=export_prefix,
        progress_context=progress_context
    )
    
    calculate_stoploss_metrics(analyzer)
    
    if print_report:
        print("\n" + "="*80)
        ResultsReporter.print_full_report(analyzer)
        
        if create_stoploss_report and analyzer.metrics.get('stoploss_count', 0) > 0:
            print_stoploss_section(analyzer)
    
    if create_stoploss_charts and analyzer.metrics.get('stoploss_count', 0) > 0:
        print(f"\n[*] Creating stop-loss analysis charts...")
        try:
            stoploss_chart_name = chart_filename.replace('.png', '_stoploss.png') if chart_filename else 'stoploss_analysis.png'
            create_stoploss_charts(analyzer, stoploss_chart_name)
        except Exception as e:
            print(f"[ERROR] Stop-loss charts failed: {e}")
    
    return analyzer


# ============================================================
# STOP-LOSS CONFIG (ENHANCED WITH COMBINED)
# ============================================================
class StopLossConfig:
    """
    Universal stop-loss configuration builder (ENHANCED)
    
    NEW METHOD:
    - combined(): Requires BOTH pl_loss AND directional conditions
    """
    
    @staticmethod
    def _normalize_pct(value):
        """Convert any number to decimal (0.30)"""
        if value >= 1:
            return value / 100
        return value
    
    @staticmethod
    def _format_pct(value):
        """Format percentage for display"""
        if value >= 1:
            return f"{value:.0f}%"
        return f"{value*100:.0f}%"
    
    @staticmethod
    def none():
        """No stop-loss"""
        return {
            'enabled': False,
            'type': 'none',
            'value': 0,
            'name': 'No Stop-Loss',
            'description': 'No stop-loss protection'
        }
    
    @staticmethod
    def fixed(pct):
        """Fixed percentage stop-loss"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        return {
            'enabled': True,
            'type': 'fixed_pct',
            'value': decimal,
            'name': f'Fixed {display}',
            'description': f'Fixed stop at {display} loss'
        }
    
    @staticmethod
    def trailing(pct, trailing_distance=None):
        """Trailing stop-loss"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        config = {
            'enabled': True,
            'type': 'trailing',
            'value': decimal,
            'name': f'Trailing {display}',
            'description': f'Trailing stop at {display} from peak'
        }
        
        if trailing_distance is not None:
            config['trailing_distance'] = StopLossConfig._normalize_pct(trailing_distance)
        
        return config
    
    @staticmethod
    def time_based(days):
        """Time-based stop"""
        return {
            'enabled': True,
            'type': 'time_based',
            'value': days,
            'name': f'Time {days}d',
            'description': f'Exit after {days} days'
        }
    
    @staticmethod
    def volatility(atr_multiplier):
        """ATR-based stop"""
        return {
            'enabled': True,
            'type': 'volatility',
            'value': atr_multiplier,
            'name': f'ATR {atr_multiplier:.1f}x',
            'description': f'Stop at {atr_multiplier:.1f}× ATR',
            'requires_atr': True
        }
    
    @staticmethod
    def pl_loss(pct):
        """P&L-based stop using real bid/ask prices"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        return {
            'enabled': True,
            'type': 'pl_loss',
            'value': decimal,
            'name': f'P&L Loss {display}',
            'description': f'Stop when P&L drops to -{display}'
        }
    
    @staticmethod
    def directional(pct):
        """Directional stop based on underlying movement"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        return {
            'enabled': True,
            'type': 'directional',
            'value': decimal,
            'name': f'Directional {display}',
            'description': f'Stop when underlying moves {display}'
        }
    
    # ========================================================
    # NEW: COMBINED STOP (REQUIRES BOTH CONDITIONS)
    # ========================================================
    
    @staticmethod
    def combined(pl_loss_pct, directional_pct):
        """
        Combined stop: Requires BOTH conditions (from code 2)
        
        Args:
            pl_loss_pct: P&L loss threshold (e.g., 5 or 0.05 = -5%)
            directional_pct: Underlying move threshold (e.g., 3 or 0.03 = 3%)
        
        Example:
            StopLossConfig.combined(5, 3)
            # Triggers only when BOTH:
            # 1. P&L drops to -5%
            # 2. Underlying moves 3% adversely
        """
        pl_decimal = StopLossConfig._normalize_pct(pl_loss_pct)
        dir_decimal = StopLossConfig._normalize_pct(directional_pct)
        
        pl_display = StopLossConfig._format_pct(pl_loss_pct)
        dir_display = StopLossConfig._format_pct(directional_pct)
        
        return {
            'enabled': True,
            'type': 'combined',
            'value': {
                'pl_loss': pl_decimal,
                'directional': dir_decimal
            },
            'name': f'Combined (P&L {pl_display} + Dir {dir_display})',
            'description': f'Stop when P&L<-{pl_display} AND underlying moves {dir_display}'
        }
    
    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================
    
    @staticmethod
    def time(days):
        """Alias for time_based()"""
        return StopLossConfig.time_based(days)
    
    @staticmethod
    def atr(multiplier):
        """Alias for volatility()"""
        return StopLossConfig.volatility(multiplier)
    
    # ========================================================
    # PRESETS (WITH COMBINED STOPS)
    # ========================================================
    
    @staticmethod
    def presets():
        """Generate all standard stop-loss presets (UPDATED WITH COMBINED)"""
        return {
            'none': StopLossConfig.none(),
            
            'fixed_20': StopLossConfig.fixed(20),
            'fixed_30': StopLossConfig.fixed(30),
            'fixed_40': StopLossConfig.fixed(40),
            'fixed_50': StopLossConfig.fixed(50),
            'fixed_70': StopLossConfig.fixed(70),
            
            'trailing_20': StopLossConfig.trailing(20),
            'trailing_30': StopLossConfig.trailing(30),
            'trailing_50': StopLossConfig.trailing(50),
            
            'time_5d': StopLossConfig.time(5),
            'time_10d': StopLossConfig.time(10),
            'time_20d': StopLossConfig.time(20),
            
            'atr_2x': StopLossConfig.atr(2.0),
            'atr_3x': StopLossConfig.atr(3.0),
            
            'pl_loss_5': StopLossConfig.pl_loss(5),
            'pl_loss_10': StopLossConfig.pl_loss(10),
            'pl_loss_15': StopLossConfig.pl_loss(15),
            
            'directional_3': StopLossConfig.directional(3),
            'directional_5': StopLossConfig.directional(5),
            'directional_7': StopLossConfig.directional(7),
            
            # NEW: COMBINED STOPS
            'combined_5_3': StopLossConfig.combined(5, 3),
            'combined_7_5': StopLossConfig.combined(7, 5),
            'combined_10_3': StopLossConfig.combined(10, 3),
        }
    
    @staticmethod
    def apply(base_config, stop_config):
        """Apply stop-loss configuration to base config"""
        merged = base_config.copy()
        
        merged['stop_loss_enabled'] = stop_config.get('enabled', False)
        
        if merged['stop_loss_enabled']:
            sl_config = {
                'type': stop_config['type'],
                'value': stop_config['value']
            }
            
            if 'trailing_distance' in stop_config:
                sl_config['trailing_distance'] = stop_config['trailing_distance']
            
            merged['stop_loss_config'] = sl_config
        
        return merged


def create_stoploss_comparison_chart(results, filename='stoploss_comparison.png', show_plots=True):
    """Create comparison chart"""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Stop-Loss Configuration Comparison', fontsize=16, fontweight='bold')
        
        names = [r['config']['name'] for r in results.values()]
        returns = [r['total_return'] for r in results.values()]
        sharpes = [r['sharpe'] for r in results.values()]
        drawdowns = [r['max_drawdown'] for r in results.values()]
        stop_counts = [r['stoploss_count'] for r in results.values()]
        
        ax1 = axes[0, 0]
        colors = ['#4CAF50' if r > 0 else '#f44336' for r in returns]
        ax1.barh(range(len(names)), returns, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_yticks(range(len(names)))
        ax1.set_yticklabels(names, fontsize=9)
        ax1.set_xlabel('Total Return (%)')
        ax1.set_title('Total Return by Stop-Loss Type', fontsize=12, fontweight='bold')
        ax1.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax1.grid(True, alpha=0.3, axis='x')
        
        ax2 = axes[0, 1]
        colors_sharpe = ['#4CAF50' if s > 1 else '#FF9800' if s > 0 else '#f44336' for s in sharpes]
        ax2.barh(range(len(names)), sharpes, color=colors_sharpe, alpha=0.7, edgecolor='black')
        ax2.set_yticks(range(len(names)))
        ax2.set_yticklabels(names, fontsize=9)
        ax2.set_xlabel('Sharpe Ratio')
        ax2.set_title('Sharpe Ratio by Stop-Loss Type', fontsize=12, fontweight='bold')
        ax2.axvline(x=1, color='green', linestyle='--', linewidth=1, label='Good (>1)')
        ax2.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='x')
        
        ax3 = axes[1, 0]
        ax3.barh(range(len(names)), drawdowns, color='#f44336', alpha=0.7, edgecolor='black')
        ax3.set_yticks(range(len(names)))
        ax3.set_yticklabels(names, fontsize=9)
        ax3.set_xlabel('Maximum Drawdown (%)')
        ax3.set_title('Maximum Drawdown (Lower is Better)', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        ax4 = axes[1, 1]
        ax4.barh(range(len(names)), stop_counts, color='#2196F3', alpha=0.7, edgecolor='black')
        ax4.set_yticks(range(len(names)))
        ax4.set_yticklabels(names, fontsize=9)
        ax4.set_xlabel('Number of Stop-Loss Exits')
        ax4.set_title('Stop-Loss Frequency', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        if show_plots:
            plt.show()
        else:
            plt.close()
        
        print(f"Comparison chart saved: {filename}")
        
    except Exception as e:
        print(f"Failed to create comparison chart: {e}")



# ============================================================
# DATA PRELOADING FUNCTION (FOR OPTIMIZATION)
# ============================================================
def preload_options_data(config, progress_widgets=None):
    """
    Предзагрузка опционных данных для оптимизации.
    Загружает данные ОДИН РАЗ и возвращает кеш.
    
    Returns:
        tuple: (lean_df, options_cache)
            - lean_df: DataFrame с историей IV lean
            - options_cache: dict {date: DataFrame} с опционными данными
    """
    if progress_widgets:
        progress_bar, status_label, monitor, start_time = progress_widgets
        status_label.value = "<b style='color:#0066cc'>🔄 Preloading options data (ONCE)...</b>"
        progress_bar.value = 5
    
    # Extract config
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    import gc
    
    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    symbol = config['symbol']
    dte_target = config.get('dte_target', 30)
    lookback_period = config.get('lookback_period', 60)
    chunk_months = config.get('chunk_months', 3)
    
    # Calculate date chunks
    data_start = start_date - timedelta(days=lookback_period + 60)
    
    date_chunks = []
    current_chunk_start = data_start
    while current_chunk_start <= end_date:
        chunk_end = min(
            current_chunk_start + timedelta(days=chunk_months * 31),
            end_date
        )
        date_chunks.append((current_chunk_start, chunk_end))
        current_chunk_start = chunk_end + timedelta(days=1)
    
    # Store lean calculations
    lean_history = []
    options_cache = {}  # {date: DataFrame with bid/ask data}
    
    # Track time for ETA
    preload_start_time = time.time()
    
    try:
        import ivolatility as ivol
        getOptionsData = ivol.setMethod('/equities/eod/options-rawiv')
        
        # Process each chunk
        for chunk_idx, (chunk_start, chunk_end) in enumerate(date_chunks):
            if progress_widgets:
                # Use update_progress for full display with ETA, CPU, RAM
                update_progress(
                    progress_bar, status_label, monitor,
                    current=chunk_idx + 1,
                    total=len(date_chunks),
                    start_time=preload_start_time,
                    message=f"🔄 Loading chunk {chunk_idx+1}/{len(date_chunks)}"
                )
            
            raw_data = getOptionsData(
                symbol=symbol,
                from_=chunk_start.strftime('%Y-%m-%d'),
                to=chunk_end.strftime('%Y-%m-%d')
            )
            
            if raw_data is None:
                continue
            
            df = pd.DataFrame(raw_data)
            
            if df.empty:
                continue
            
            # Essential columns
            essential_cols = ['date', 'expiration', 'strike', 'Call/Put', 'iv', 'Adjusted close']
            if 'bid' in df.columns:
                essential_cols.append('bid')
            if 'ask' in df.columns:
                essential_cols.append('ask')

            df = df[essential_cols].copy()
            
            # Process bid/ask
            if 'bid' in df.columns:
                df['bid'] = pd.to_numeric(df['bid'], errors='coerce').astype('float32')
            else:
                df['bid'] = np.nan

            if 'ask' in df.columns:
                df['ask'] = pd.to_numeric(df['ask'], errors='coerce').astype('float32')
            else:
                df['ask'] = np.nan

            # Calculate mid price
            df['mid'] = (df['bid'] + df['ask']) / 2
            df['mid'] = df['mid'].fillna(df['iv'])
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['expiration'] = pd.to_datetime(df['expiration']).dt.date
            df['strike'] = pd.to_numeric(df['strike'], errors='coerce').astype('float32')
            df['iv'] = pd.to_numeric(df['iv'], errors='coerce').astype('float32')
            df['Adjusted close'] = pd.to_numeric(df['Adjusted close'], errors='coerce').astype('float32')
            
            df['dte'] = (pd.to_datetime(df['expiration']) - pd.to_datetime(df['date'])).dt.days
            df['dte'] = df['dte'].astype('int16')
            
            df = df.dropna(subset=['strike', 'iv', 'Adjusted close'])
            
            if df.empty:
                del df
                gc.collect()
                continue

            # Cache options data for position tracking
            for date_val in df['date'].unique():
                if date_val not in options_cache:
                    options_cache[date_val] = df[df['date'] == date_val].copy()
            
            # Calculate lean for this chunk
            trading_dates = sorted(df['date'].unique())
            
            for current_date in trading_dates:
                day_data = df[df['date'] == current_date]
                
                if day_data.empty:
                    continue
                
                stock_price = float(day_data['Adjusted close'].iloc[0])
                
                dte_filtered = day_data[
                    (day_data['dte'] >= dte_target - 7) & 
                    (day_data['dte'] <= dte_target + 7)
                ]
                
                if dte_filtered.empty:
                    continue
                
                dte_filtered = dte_filtered.copy()
                dte_filtered['strike_diff'] = abs(dte_filtered['strike'] - stock_price)
                atm_idx = dte_filtered['strike_diff'].idxmin()
                atm_strike = float(dte_filtered.loc[atm_idx, 'strike'])
                
                atm_options = dte_filtered[dte_filtered['strike'] == atm_strike]
                atm_call = atm_options[atm_options['Call/Put'] == 'C']
                atm_put = atm_options[atm_options['Call/Put'] == 'P']
                
                if not atm_call.empty and not atm_put.empty:
                    call_iv = float(atm_call['iv'].iloc[0])
                    put_iv = float(atm_put['iv'].iloc[0])
                    
                    if pd.notna(call_iv) and pd.notna(put_iv) and call_iv > 0 and put_iv > 0:
                        iv_lean = call_iv - put_iv
                        
                        lean_history.append({
                            'date': current_date,
                            'stock_price': stock_price,
                            'iv_lean': iv_lean
                        })
            
            del df, raw_data
            gc.collect()
        
        lean_df = pd.DataFrame(lean_history)
        lean_df['stock_price'] = lean_df['stock_price'].astype('float32')
        lean_df['iv_lean'] = lean_df['iv_lean'].astype('float32')
        
        del lean_history
        gc.collect()
        
        if progress_widgets:
            status_label.value = f"<b style='color:#00cc00'>✓ Data preloaded: {len(lean_df)} days, {len(options_cache)} cached dates</b>"
            progress_bar.value = 35
        
        print(f"✓ Data preloaded: {len(lean_df)} days, {len(options_cache)} cached dates")
        
        return lean_df, options_cache
        
    except Exception as e:
        print(f"Error preloading data: {e}")
        return pd.DataFrame(), {}


# ============================================================
# NEW: OPTIMIZATION FRAMEWORK
# ============================================================
def optimize_parameters(base_config, param_grid, strategy_function,
                       optimization_metric='sharpe', min_trades=5,
                       max_drawdown_limit=None, parallel=False,
                       export_each_combo=True # ← НОВЫЙ ПАРАМЕТР
                       ):  
    """
    Optimize strategy parameters across multiple combinations
    
    Args:
        base_config: Base configuration dict
        param_grid: Dict of parameters to optimize
            Example: {'z_score_entry': [1.0, 1.5, 2.0], 'z_score_exit': [0.1, 0.3, 0.5]}
        strategy_function: Strategy function to run
        optimization_metric: Metric to optimize ('sharpe', 'total_return', 'profit_factor', 'calmar')
        min_trades: Minimum number of trades required
        max_drawdown_limit: Maximum acceptable drawdown (e.g., 0.10 for 10%)
        parallel: Use parallel processing (not implemented yet)
        export_each_combo: If True, exports files for each combination  # ← 
    
    Returns:
        tuple: (results_df, best_params, results_folder)
    """
    
    # ═══ ДОБАВИТЬ В НАЧАЛО ФУНКЦИИ ═══
    # Create results folder
    results_folder = create_optimization_folder()
    print(f"📊 Results will be saved to: {results_folder}\n")
    
    # Record start time
    optimization_start_time = datetime.now()
    start_time_str = optimization_start_time.strftime('%Y-%m-%d %H:%M:%S')
    
    print("\n" + "="*80)
    print(" "*20 + "PARAMETER OPTIMIZATION")
    print("="*80)
    print(f"Strategy: {base_config.get('strategy_name', 'Unknown')}")
    print(f"Period: {base_config.get('start_date')} to {base_config.get('end_date')}")
    print(f"Optimization Metric: {optimization_metric}")
    print(f"Min Trades: {min_trades}")
    print(f"🕐 Started: {start_time_str}")
    if max_drawdown_limit:
        print(f"Max Drawdown Limit: {max_drawdown_limit*100:.0f}%")
    print("="*80 + "\n")
    
    # Generate all combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_combinations = list(product(*param_values))
    
    total_combinations = len(all_combinations)
    print(f"Testing {total_combinations} parameter combinations...")
    print(f"Parameters: {param_names}")
    print(f"Grid: {param_grid}\n")
    
    # Create SHARED progress context for all backtests
    try:
        from IPython.display import display
        import ipywidgets as widgets
        
        progress_bar = widgets.FloatProgress(
            value=0, min=0, max=100,
            description='Optimizing:',
            bar_style='info',
            layout=widgets.Layout(width='100%', height='30px')
        )
        
        status_label = widgets.HTML(value="<b>Starting optimization...</b>")
        display(widgets.VBox([progress_bar, status_label]))
        
        monitor = ResourceMonitor()
        opt_start_time = time.time()
        
        # Create shared progress context (will suppress individual backtest progress)
        shared_progress = {
            'progress_widgets': (progress_bar, status_label, monitor, opt_start_time),
            'is_optimization': True
        }
        has_widgets = True
    except:
        shared_progress = None
        has_widgets = False
        print("Running optimization (no progress bar)...")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PRELOAD DATA ONCE (FOR ALL OPTIMIZATION ITERATIONS)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print("📥 PRELOADING OPTIONS DATA (loads ONCE, reused for all combinations)")
    print("="*80)
    
    preloaded_lean_df, preloaded_options_cache = preload_options_data(
        base_config, 
        progress_widgets=shared_progress['progress_widgets'] if shared_progress else None
    )
    
    if preloaded_lean_df.empty:
        print("\n❌ ERROR: Failed to preload data. Cannot proceed with optimization.")
        return pd.DataFrame(), None
    
    print(f"✓ Preloading complete! Data will be reused for all {total_combinations} combinations")
    print("="*80 + "\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RESET PROGRESS BAR FOR OPTIMIZATION LOOP
    # ═══════════════════════════════════════════════════════════════════════════
    if has_widgets:
        progress_bar.value = 0
        progress_bar.bar_style = 'info'
        status_label.value = "<b style='color:#0066cc'>Starting optimization loop...</b>"
    
    # Run backtests
    results = []
    start_time = time.time()
    
    for idx, param_combo in enumerate(all_combinations, 1):
        # Create test config
        test_config = base_config.copy()
        
        # Update parameters
        for param_name, param_value in zip(param_names, param_combo):
            test_config[param_name] = param_value
        
        # Update name
        param_str = "_".join([f"{k}={v}" for k, v in zip(param_names, param_combo)])
        test_config['strategy_name'] = f"{base_config.get('strategy_name', 'Strategy')} [{param_str}]"
        
        # ═══ ADD PRELOADED DATA TO CONFIG ═══
        test_config['_preloaded_lean_df'] = preloaded_lean_df
        test_config['_preloaded_options_cache'] = preloaded_options_cache
        
        # Update progress
        if has_widgets:
            # Use update_progress for full display with ETA, CPU, RAM
            update_progress(
                progress_bar, status_label, monitor,
                current=idx,
                total=total_combinations,
                start_time=start_time,
                message=f"Testing: {param_str}"
            )
        else:
            if idx % max(1, total_combinations // 10) == 0:
                print(f"[{idx}/{total_combinations}] {param_str}")
        
        # ═══ ИЗМЕНИТЬ ВЫЗОВ run_backtest (строки ~2240-2248) ═══
        try:
            # Create compact parameter string (e.g., Z1.0_E0.1_PT20)
            param_parts = []
            for name, value in zip(param_names, param_combo):
                if 'z_score_entry' in name:
                    param_parts.append(f"Z{value}")
                elif 'z_score_exit' in name:
                    param_parts.append(f"E{value}")
                elif 'profit_target' in name:
                    if value is None:
                        param_parts.append("PTNo")
                    else:
                        param_parts.append(f"PT{int(value*100)}")
                elif 'min_days' in name:
                    param_parts.append(f"D{value}")
                else:
                    # Generic short name for other params
                    short_name = ''.join([c for c in name if c.isupper() or c.isdigit()])[:3]
                    param_parts.append(f"{short_name}{value}")
            
            compact_params = "_".join(param_parts)
            
            # Create combo folder: c01_Z1.0_E0.1_PT20
            combo_folder = os.path.join(results_folder, f'c{idx:02d}_{compact_params}')
            os.makedirs(combo_folder, exist_ok=True)
            
            # File prefix: c01_Z1.0_E0.1_PT20
            combo_prefix = f"c{idx:02d}_{compact_params}"
            
            # Run backtest WITH EXPORT AND CHARTS (saved but not displayed)
            analyzer = run_backtest(
                strategy_function,
                test_config,
                print_report=False,
                create_charts=export_each_combo,  # ← СОЗДАЕМ ГРАФИКИ (сохраняются, но не показываются)
                export_results=export_each_combo,  # ← ИЗМЕНЕНО
                progress_context=shared_progress,
                chart_filename=os.path.join(combo_folder, 'equity_curve.png') if export_each_combo else None,  # ← ГРАФИКИ СОХРАНЯЮТСЯ
                export_prefix=os.path.join(combo_folder, combo_prefix) if export_each_combo else None  # ← ДОБАВЛЕНО
            )
            
            # Check validity
            is_valid = True
            invalid_reason = ""
            
            if analyzer.metrics['total_trades'] < min_trades:
                is_valid = False
                invalid_reason = f"Too few trades ({analyzer.metrics['total_trades']})"
            
            if max_drawdown_limit and analyzer.metrics['max_drawdown'] > (max_drawdown_limit * 100):
                is_valid = False
                invalid_reason = f"Excessive drawdown ({analyzer.metrics['max_drawdown']:.1f}%)"
            
            # Print compact statistics for this combination
            status_symbol = "✓" if is_valid else "✗"
            status_color = "#00cc00" if is_valid else "#ff6666"
            
            print(f"\n[{idx}/{total_combinations}] {param_str}")
            print("-" * 80)
            if is_valid:
                print(f"  {status_symbol} Return: {analyzer.metrics['total_return']:>7.2f}% | "
                      f"Sharpe: {analyzer.metrics['sharpe']:>6.2f} | "
                      f"Max DD: {analyzer.metrics['max_drawdown']:>6.2f}% | "
                      f"Trades: {analyzer.metrics['total_trades']:>3} | "
                      f"Win Rate: {analyzer.metrics['win_rate']:>5.1f}% | "
                      f"PF: {analyzer.metrics['profit_factor']:>5.2f}")
            else:
                print(f"  {status_symbol} INVALID: {invalid_reason}")
            
            # Update widget status with last result
            if has_widgets:
                result_text = f"Return: {analyzer.metrics['total_return']:.1f}% | Sharpe: {analyzer.metrics['sharpe']:.2f}" if is_valid else invalid_reason
                
                # Get resource usage
                cpu_pct = monitor.get_cpu_percent()
                mem_info = monitor.get_memory_info()
                ram_mb = mem_info[0]  # process_mb
                resource_text = f"CPU: {cpu_pct:.0f}% | RAM: {ram_mb:.0f}MB"
                
                status_label.value = (
                    f"<b style='color:{status_color}'>[{idx}/{total_combinations}] {param_str}</b><br>"
                    f"<span style='color:#666'>{result_text}</span><br>"
                    f"<span style='color:#999;font-size:10px'>{resource_text}</span>"
                )
            
            # Store results
            result = {
                'combination_id': idx,
                'is_valid': is_valid,
                'invalid_reason': invalid_reason,
                **{name: value for name, value in zip(param_names, param_combo)},
                'total_return': analyzer.metrics['total_return'],
                'sharpe': analyzer.metrics['sharpe'],
                'sortino': analyzer.metrics['sortino'],
                'calmar': analyzer.metrics['calmar'],
                'max_drawdown': analyzer.metrics['max_drawdown'],
                'win_rate': analyzer.metrics['win_rate'],
                'profit_factor': analyzer.metrics['profit_factor'],
                'total_trades': analyzer.metrics['total_trades'],
                'avg_win': analyzer.metrics['avg_win'],
                'avg_loss': analyzer.metrics['avg_loss'],
                'volatility': analyzer.metrics['volatility'],
            }
            
            results.append(result)
            
            # Show intermediate summary every 10 combinations (or at end)
            if idx % 10 == 0 or idx == total_combinations:
                valid_so_far = [r for r in results if r['is_valid']]
                if valid_so_far:
                    print("\n" + "="*80)
                    print(f"INTERMEDIATE SUMMARY ({idx}/{total_combinations} tested)")
                    print("="*80)
                    
                    # Sort by optimization metric
                    if optimization_metric == 'sharpe':
                        valid_so_far.sort(key=lambda x: x['sharpe'], reverse=True)
                    elif optimization_metric == 'total_return':
                        valid_so_far.sort(key=lambda x: x['total_return'], reverse=True)
                    elif optimization_metric == 'profit_factor':
                        valid_so_far.sort(key=lambda x: x['profit_factor'], reverse=True)
                    elif optimization_metric == 'calmar':
                        valid_so_far.sort(key=lambda x: x['calmar'], reverse=True)
                    
                    # Show top 3
                    print(f"\n🏆 TOP 3 BY {optimization_metric.upper()}:")
                    print("-"*80)
                    for rank, res in enumerate(valid_so_far[:3], 1):
                        params_display = ", ".join([f"{name}={res[name]}" for name in param_names])
                        print(f"  {rank}. [{params_display}]")
                        print(f"     Return: {res['total_return']:>7.2f}% | "
                              f"Sharpe: {res['sharpe']:>6.2f} | "
                              f"Max DD: {res['max_drawdown']:>6.2f}% | "
                              f"Trades: {res['total_trades']:>3}")
                    
                    print(f"\nValid: {len(valid_so_far)}/{idx} | "
                          f"Invalid: {idx - len(valid_so_far)}/{idx}")
                    print("="*80 + "\n")
        
        except Exception as e:
            print(f"\n[{idx}/{total_combinations}] {param_str}")
            print("-" * 80)
            print(f"  ✗ ERROR: {str(e)[:100]}")
            
            result = {
                'combination_id': idx,
                'is_valid': False,
                'invalid_reason': f"Error: {str(e)[:50]}",
                **{name: value for name, value in zip(param_names, param_combo)},
                'total_return': 0, 'sharpe': 0, 'sortino': 0, 'calmar': 0,
                'max_drawdown': 0, 'win_rate': 0, 'profit_factor': 0,
                'total_trades': 0, 'avg_win': 0, 'avg_loss': 0, 'volatility': 0
            }
            results.append(result)
    
    elapsed = time.time() - start_time
    
    if has_widgets:
        progress_bar.value = 100
        progress_bar.bar_style = 'success'
        status_label.value = f"<b style='color:#00cc00'>✓ Optimization complete in {int(elapsed)}s</b>"
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Round numeric columns to 2 decimals
    numeric_columns = results_df.select_dtypes(include=['float64', 'float32', 'float']).columns
    for col in numeric_columns:
        results_df[col] = results_df[col].round(5)

    # ═══ ДОБАВИТЬ СОХРАНЕНИЕ SUMMARY В ПАПКУ ═══
    summary_path = os.path.join(results_folder, 'optimization_summary.csv')
    results_df.to_csv(summary_path, index=False)
    print(f"\n✓ Summary saved: {summary_path}")
    
    # Find best parameters
    valid_results = results_df[results_df['is_valid'] == True].copy()
    
    if len(valid_results) == 0:
        print("\n" + "="*80)
        print("WARNING: No valid combinations found!")
        print("Try relaxing constraints or checking parameter ranges")
        print("="*80)
        return results_df, None, results_folder
    
    # Select best based on metric
    if optimization_metric == 'sharpe':
        best_idx = valid_results['sharpe'].idxmax()
    elif optimization_metric == 'total_return':
        best_idx = valid_results['total_return'].idxmax()
    elif optimization_metric == 'profit_factor':
        best_idx = valid_results['profit_factor'].idxmax()
    elif optimization_metric == 'calmar':
        best_idx = valid_results['calmar'].idxmax()
    else:
        best_idx = valid_results['sharpe'].idxmax()
    
    best_result = valid_results.loc[best_idx]
    
    # Extract best parameters
    best_params = {name: best_result[name] for name in param_names}
    
    # Calculate total time
    optimization_end_time = datetime.now()
    total_duration = optimization_end_time - optimization_start_time
    end_time_str = optimization_end_time.strftime('%Y-%m-%d %H:%M:%S')
    duration_str = format_time(total_duration.total_seconds())
    
    # Print summary
    print("="*80)
    print(" "*20 + "OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"\nTotal Combinations Tested: {total_combinations}")
    print(f"Valid Combinations: {len(valid_results)}")
    print(f"Invalid Combinations: {len(results_df) - len(valid_results)}")
    print(f"🕐 Started: {start_time_str}")
    print(f"🕐 Finished: {end_time_str}")
    print(f"⏱️ Total Duration: {duration_str}")
    
    print(f"\n{'='*80}")
    print(" "*20 + "BEST PARAMETERS")
    print("="*80)
    for param_name, param_value in best_params.items():
        print(f"{param_name:25s}: {param_value}")
    
    print(f"\n{'='*80}")
    print(" "*20 + "BEST PERFORMANCE")
    print("="*80)
    print(f"Total Return:        {best_result['total_return']:>10.2f}%")
    print(f"Sharpe Ratio:        {best_result['sharpe']:>10.2f}")
    print(f"Sortino Ratio:       {best_result['sortino']:>10.2f}")
    print(f"Calmar Ratio:        {best_result['calmar']:>10.2f}")
    print(f"Max Drawdown:        {best_result['max_drawdown']:>10.2f}%")
    print(f"Win Rate:            {best_result['win_rate']:>10.1f}%")
    print(f"Profit Factor:       {best_result['profit_factor']:>10.2f}")
    print(f"Total Trades:        {best_result['total_trades']:>10.0f}")
    print(f"Avg Win:             ${best_result['avg_win']:>10.2f}")
    print(f"Avg Loss:            ${best_result['avg_loss']:>10.2f}")
    print("="*80)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # НОВОЕ! ПОЛНЫЙ БЭКТЕСТ ЛУЧШЕЙ КОМБИНАЦИИ СО ВСЕМИ ГРАФИКАМИ
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(" "*15 + "RUNNING FULL BACKTEST FOR BEST COMBINATION")
    print("="*80)
    print("\n📊 Creating detailed report for best combination...")
    print(f"Parameters: {', '.join([f'{k}={v}' for k, v in best_params.items()])}\n")
    
    # Create config for best combination
    best_config = base_config.copy()
    best_config.update(best_params)
    best_config['_preloaded_lean_df'] = preloaded_lean_df
    best_config['_preloaded_options_cache'] = preloaded_options_cache
    
    # Create folder for best combination
    best_combo_folder = os.path.join(results_folder, 'best_combination')
    os.makedirs(best_combo_folder, exist_ok=True)
    
    # Run FULL backtest with ALL charts and exports
    # Note: progress_context=None, so plt.show() will be called but fail due to renderer
    # We'll display charts explicitly afterwards using IPython.display.Image
    best_analyzer = run_backtest(
        strategy_function,
        best_config,
        print_report=True,  # ← ПОКАЗЫВАЕМ ПОЛНЫЙ ОТЧЕТ
        create_charts=True,  # ← СОЗДАЕМ ВСЕ ГРАФИКИ
        export_results=True,  # ← ЭКСПОРТИРУЕМ ВСЕ ФАЙЛЫ
        progress_context=None,  # ← Обычный режим
        chart_filename=os.path.join(best_combo_folder, 'equity_curve.png'),
        export_prefix=os.path.join(best_combo_folder, 'best')
    )
    
    # Save detailed metrics to optimization_metrics.csv
    metrics_data = {
        'metric': list(best_analyzer.metrics.keys()),
        'value': list(best_analyzer.metrics.values())
    }
    metrics_df = pd.DataFrame(metrics_data)
    metrics_path = os.path.join(results_folder, 'optimization_metrics.csv')
    metrics_df.to_csv(metrics_path, index=False)
    
    print(f"\n✓ Detailed metrics saved: {metrics_path}")
    print(f"✓ Best combination results saved to: {best_combo_folder}/")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ОТОБРАЖЕНИЕ ГРАФИКОВ ЛУЧШЕЙ КОМБИНАЦИИ В NOTEBOOK
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        # Charts are displayed in the notebook, not here
        chart_file = os.path.join(best_combo_folder, 'equity_curve.png')
        if os.path.exists(chart_file):
            print(f"\n📈 Best combination charts saved to: {chart_file}")
    except Exception as e:
        print(f"\n⚠ Could not display charts (saved to {best_combo_folder}/): {e}")
    
    print("="*80 + "\n")
    
    return results_df, best_params, results_folder


def plot_optimization_results(results_df, param_names, filename='optimization_results.png'):
    """
    Create visualization of optimization results
    
    Args:
        results_df: Results DataFrame from optimize_parameters()
        param_names: List of parameter names
        filename: Output filename
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    valid_results = results_df[results_df['is_valid'] == True].copy()
    
    if valid_results.empty:
        print("No valid results to plot")
        return
    
    sns.set_style("whitegrid")
    
    fig = plt.figure(figsize=(18, 12))
    
    # 1. Sharpe vs Total Return scatter
    ax1 = plt.subplot(2, 3, 1)
    scatter = ax1.scatter(
        valid_results['total_return'],
        valid_results['sharpe'],
        c=valid_results['max_drawdown'],
        s=valid_results['total_trades']*10,
        alpha=0.6,
        cmap='RdYlGn_r'
    )
    ax1.set_xlabel('Total Return (%)', fontsize=10)
    ax1.set_ylabel('Sharpe Ratio', fontsize=10)
    ax1.set_title('Sharpe vs Return (size=trades, color=drawdown)', fontsize=11, fontweight='bold')
    plt.colorbar(scatter, ax=ax1, label='Max Drawdown (%)')
    ax1.grid(True, alpha=0.3)
    
    # 2. Parameter heatmap (if 2 parameters)
    if len(param_names) == 2:
        ax2 = plt.subplot(2, 3, 2)
        pivot_data = valid_results.pivot_table(
            values='sharpe',
            index=param_names[0],
            columns=param_names[1],
            aggfunc='mean'
        )
        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlGn', ax=ax2)
        ax2.set_title(f'Sharpe Ratio Heatmap', fontsize=11, fontweight='bold')
    else:
        ax2 = plt.subplot(2, 3, 2)
        ax2.text(0.5, 0.5, 'Heatmap requires\nexactly 2 parameters',
                ha='center', va='center', fontsize=12)
        ax2.axis('off')
    
    # 3. Win Rate vs Profit Factor
    ax3 = plt.subplot(2, 3, 3)
    scatter3 = ax3.scatter(
        valid_results['win_rate'],
        valid_results['profit_factor'],
        c=valid_results['sharpe'],
        s=100,
        alpha=0.6,
        cmap='viridis'
    )
    ax3.set_xlabel('Win Rate (%)', fontsize=10)
    ax3.set_ylabel('Profit Factor', fontsize=10)
    ax3.set_title('Win Rate vs Profit Factor (color=Sharpe)', fontsize=11, fontweight='bold')
    plt.colorbar(scatter3, ax=ax3, label='Sharpe Ratio')
    ax3.grid(True, alpha=0.3)
    
    # 4. Distribution of Sharpe Ratios
    ax4 = plt.subplot(2, 3, 4)
    ax4.hist(valid_results['sharpe'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax4.axvline(valid_results['sharpe'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax4.axvline(valid_results['sharpe'].median(), color='green', linestyle='--', linewidth=2, label='Median')
    ax4.set_xlabel('Sharpe Ratio', fontsize=10)
    ax4.set_ylabel('Frequency', fontsize=10)
    ax4.set_title('Distribution of Sharpe Ratios', fontsize=11, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Total Trades distribution
    ax5 = plt.subplot(2, 3, 5)
    ax5.hist(valid_results['total_trades'], bins=15, color='coral', alpha=0.7, edgecolor='black')
    ax5.set_xlabel('Total Trades', fontsize=10)
    ax5.set_ylabel('Frequency', fontsize=10)
    ax5.set_title('Distribution of Trade Counts', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Top 10 combinations
    ax6 = plt.subplot(2, 3, 6)
    top_10 = valid_results.nlargest(10, 'sharpe')[['combination_id', 'sharpe']].sort_values('sharpe')
    ax6.barh(range(len(top_10)), top_10['sharpe'], color='green', alpha=0.7)
    ax6.set_yticks(range(len(top_10)))
    ax6.set_yticklabels([f"#{int(x)}" for x in top_10['combination_id']])
    ax6.set_xlabel('Sharpe Ratio', fontsize=10)
    ax6.set_title('Top 10 Combinations by Sharpe', fontsize=11, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: {filename}")
    plt.close()  # Закрываем без показа, так как отображаем через display(Image)


# Export all
__all__ = [
    'BacktestResults', 'BacktestAnalyzer', 'ResultsReporter',
    'ChartGenerator', 'ResultsExporter', 'run_backtest', 'run_backtest_with_stoploss',
    'init_api', 'api_call', 'APIHelper', 'APIManager',
    'ResourceMonitor', 'create_progress_bar', 'update_progress', 'format_time',
    'StopLossManager', 'PositionManager', 'StopLossConfig',
    'calculate_stoploss_metrics', 'print_stoploss_section', 'create_stoploss_charts',
    'create_stoploss_comparison_chart',
    'optimize_parameters', 'plot_optimization_results',
    'create_optimization_folder',
    'preload_options_data'  # ← ДОБАВЛЕНО
]