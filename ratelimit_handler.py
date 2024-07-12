# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 03:10:27 2024

@author: ketch
"""

import asyncio, copy

class RateLimiter() :
    def __init__(self, unit_time = 1000, default_rl = 10) :
        self.unit_time = unit_time # In milliseconds
        self.requests = {} # {func_id: {'ratelimit': ..., 'requests': ...}}
        
        self.default_rl = default_rl
        return
    
    async def reset_requests(self, func) :
        func_name = func.__name__
        while not self.requests[func_name]['freed?'] :
            await asyncio.sleep(self.unit_time / 1000)
            
            self.requests[func_name]['requests'] = 0
            
            try :
                pending_requests = copy.deepcopy(self.requests[func_name]['pending_requests'])
            except TypeError :
                # When the function/method cannot be pickled.
                pending_requests = self.requests[func_name]['pending_requests'].copy()
            self.requests[func_name]['pending_requests'].clear()
            
            for req in pending_requests :
                if req['type'] == 'func_call' :
                    await self.handle(func)(*req['args'], **req['kwargs'])
                    continue
                elif req['type'] == 'free' :
                    func_info = self.requests[func_name]
                    if func_info['requests'] >= func_info['ratelimit'] :
                        await self.free(func)
                    else :
                        self.requests[func_name]['reset_request_task'].cancel()
                        try :
                            await self.requests[func_name]['reset_request_task']
                        except asyncio.CancelledError :
                            pass
                        
                        del self.requests[func_name]
                        self.requests[func_name]['freed?'] = True
                    break
            continue
        return
    
    def handle(self, func, default_rl = None) :
        func_name = func.__name__
        if func_name in self.requests :
            func_info = self.requests[func_name]
            if func_info['requests'] >= func_info['ratelimit'] :
                async def ratelimited_func(*args, **kwargs) :
                    self.requests[func_name]['pending_requests'].append({'type': 'func_call', 'func': func, 'args': args, 'kwargs': kwargs})
                    return
            else :
                async def ratelimited_func(*args, **kwargs) :
                    self.requests[func_name]['requests'] += 1
                    return (await func(*args, **kwargs))
            return ratelimited_func
        else :
            self.requests[func_name] = {'ratelimit': (default_rl or self.default_rl), 'requests': 0, 'pending_requests': [], 'reset_request_task': None, 'func': func, 'func_name': func_name, 'freed?': False}
            self.requests[func_name]['reset_request_task'] = asyncio.create_task(self.reset_requests(func))
            async def ratelimited_func(*args, **kwargs) :
                self.requests[func_name]['requests'] += 1
                return (await func(*args, **kwargs))
            return ratelimited_func
    
    def ratelimit(self, rl = 10) :
        def decorator(func) :
            func_name = func.__name__
            self.requests[func_name] = {'ratelimit': rl, 'requests': 0, 'pending_requests': [], 'reset_request_task': None, 'func': func, 'func_name': func_name, 'freed?': False}
            self.requests[func_name]['reset_request_task'] = asyncio.create_task(self.reset_requests(func))
            async def ratelimited_func(*args, **kwargs) :
                handled_func = self.handle(func)
                return (await handled_func(*args, **kwargs))
            return ratelimited_func 
        return decorator
    
    async def free(self, func) :
        func_name = func.__name__
        if func_name in self.requests :
            self.requests[func_name]['pending_requests'].append({'type': 'free', 'func': None, 'args': [], 'kwargs': {}})
            return True
        return False
    
    pass