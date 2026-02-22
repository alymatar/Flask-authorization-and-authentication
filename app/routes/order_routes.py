"""
Маршруты для демонстрации системы разрешений (тестовые данные)
"""
from flask import Blueprint, request, jsonify
from app.utils.decorators import login_required, permission_required

order_bp = Blueprint('orders', __name__)

# Тестовые данные заказов
MOCK_ORDERS = [
    {'id': 1, 'customer_id': 1, 'total': 250.00, 'status': 'pending', 'items': 3},
    {'id': 2, 'customer_id': 2, 'total': 89.99, 'status': 'shipped', 'items': 1},
    {'id': 3, 'customer_id': 1, 'total': 150.00, 'status': 'delivered', 'items': 2},
    {'id': 4, 'customer_id': 3, 'total': 499.99, 'status': 'pending', 'items': 4},
]

@order_bp.route('', methods=['GET'])
@login_required
@permission_required('orders', 'read')
def get_orders():
    """Получение списка заказов с фильтрацией по правам доступа."""
    user = request.user
    
    if user.has_permission('orders', 'read_all'):
        orders = MOCK_ORDERS
    else:
        orders = [o for o in MOCK_ORDERS if o['customer_id'] == user.id]
    
    return jsonify({
        'orders': orders,
        'count': len(orders)
    })

@order_bp.route('/<int:order_id>', methods=['GET'])
@login_required
@permission_required('orders', 'read')
def get_order(order_id):
    """Получение одного заказа по ID"""
    order = next((o for o in MOCK_ORDERS if o['id'] == order_id), None)
    
    if not order:
        return jsonify({'error': 'Заказ не найден'}), 404
    
    user = request.user
    
    if not user.has_permission('orders', 'read', order['customer_id']):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({'order': order})

@order_bp.route('', methods=['POST'])
@login_required
@permission_required('orders', 'create')
def create_order():
    """Создание нового заказа."""
    user = request.user
    data = request.get_json()
    
    if not data.get('items'):
        return jsonify({'error': 'Требуются товары заказа'}), 400
    
    new_order = {
        'id': len(MOCK_ORDERS) + 1,
        'customer_id': user.id,
        'total': data.get('total', 0),
        'status': 'pending',
        'items': data.get('items', [])
    }
    
    MOCK_ORDERS.append(new_order)
    
    return jsonify({
        'message': 'Заказ успешно создан',
        'order': new_order
    }), 201

@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
@permission_required('orders', 'update')
def cancel_order(order_id):
    """Отмена заказа"""
    order = next((o for o in MOCK_ORDERS if o['id'] == order_id), None)
    
    if not order:
        return jsonify({'error': 'Заказ не найден'}), 404
    
    user = request.user
    
    if not user.has_permission('orders', 'update', order['customer_id']):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if order['status'] == 'delivered':
        return jsonify({'error': 'Нельзя отменить доставленный заказ'}), 400
    
    order['status'] = 'cancelled'
    
    return jsonify({
        'message': 'Заказ успешно отменен',
        'order': order
    })