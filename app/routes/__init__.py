"""
Пакет маршрутов 
"""
from flask import Blueprint

def create_response(data=None, message=None, status=200, meta=None):
    """
    Вспомогательная функция для получения согласованных ответов API
    """
    response = {}
    
    if data is not None:
        response['data'] = data
    
    if message is not None:
        response['message'] = message
    
    if meta is not None:
        response['meta'] = meta
    
    if not response:
        response = {'message': 'Success'}
    
    return response, status