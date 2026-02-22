"""
Маршруты для демонстрации системы разрешений (тестовые данные товаров)
"""
from flask import Blueprint, request, jsonify
from app.utils.decorators import login_required, permission_required

product_bp = Blueprint('products', __name__)

# Тестовые данные товаров
MOCK_PRODUCTS = [
    {'id': 1, 'name': 'Laptop', 'owner_id': 1, 'price': 999.99, 'category': 'Electronics'},
    {'id': 2, 'name': 'Mouse', 'owner_id': 2, 'price': 29.99, 'category': 'Electronics'},
    {'id': 3, 'name': 'Desk', 'owner_id': 1, 'price': 299.99, 'category': 'Furniture'},
    {'id': 4, 'name': 'Chair', 'owner_id': 3, 'price': 149.99, 'category': 'Furniture'},
    {'id': 5, 'name': 'Monitor', 'owner_id': 2, 'price': 399.99, 'category': 'Electronics'},
]

@product_bp.route('', methods=['GET'])
@login_required
@permission_required('products', 'read')
def get_products():
    """Получение списка товаров с фильтрацией по правам доступа"""
    user = request.user
    
    if user.has_permission('products', 'read_all'):
        products = MOCK_PRODUCTS
    else:
        products = [p for p in MOCK_PRODUCTS if p['owner_id'] == user.id]
    
    return jsonify({
        'products': products,
        'count': len(products)
    })

@product_bp.route('/<int:product_id>', methods=['GET'])
@login_required
@permission_required('products', 'read')
def get_product(product_id):
    """Получение одного товара по ID"""
    product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404
    
    user = request.user
    if not user.has_permission('products', 'read', product['owner_id']):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({'product': product})

@product_bp.route('', methods=['POST'])
@login_required
@permission_required('products', 'create')
def create_product():
    """Создание нового товара"""
    user = request.user
    data = request.get_json()
    
    if not data.get('name') or not data.get('price'):
        return jsonify({'error': 'Требуются название и цена'}), 400
    
    new_product = {
        'id': len(MOCK_PRODUCTS) + 1,
        'name': data['name'],
        'price': data['price'],
        'category': data.get('category', 'Other'),
        'owner_id': user.id
    }
    MOCK_PRODUCTS.append(new_product)
    
    return jsonify({
        'message': 'Товар успешно создан',
        'product': new_product
    }), 201

@product_bp.route('/<int:product_id>', methods=['PUT'])
@login_required
@permission_required('products', 'update')
def update_product(product_id):
    """Обновление товара"""
    product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404
    
    user = request.user
    if not user.has_permission('products', 'update', product['owner_id']):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    
    if 'name' in data:
        product['name'] = data['name']
    if 'price' in data:
        product['price'] = data['price']
    if 'category' in data:
        product['category'] = data['category']
    
    return jsonify({
        'message': 'Товар успешно обновлен',
        'product': product
    })

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@login_required
@permission_required('products', 'delete')
def delete_product(product_id):
    """Удаление товара"""
    product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404
    
    user = request.user
    if not user.has_permission('products', 'delete', product['owner_id']):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    MOCK_PRODUCTS.remove(product)
    
    return jsonify({'message': 'Товар успешно удален'})