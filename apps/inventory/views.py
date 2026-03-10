from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .models import Product, ProductCategory, StockRecord, StockCheck, StockCheckDetail, Warehouse, WarehouseCategory, InventoryTabConfig
from .serializers import (
    ProductSerializer, ProductCategorySerializer,
    StockRecordSerializer, StockCheckSerializer, WarehouseSerializer,
    WarehouseCategorySerializer, InventoryTabConfigSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """产品视图集"""

    queryset = Product.objects.filter(is_active=True).order_by('-id')
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(specification__icontains=search)
            )
        
        product_type = self.request.query_params.get('product_type', None)
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 检查库存预警
        low_stock = self.request.query_params.get('low_stock', None)
        if low_stock:
            queryset = queryset.filter(
                product__stock_records__quantity__lt=F('min_stock')
            )
        
        return queryset


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """产品分类视图集"""
    
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


class StockRecordViewSet(viewsets.ModelViewSet):
    """库存记录视图集"""

    queryset = StockRecord.objects.filter(is_deleted=False).order_by('-operate_time')
    serializer_class = StockRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        product_id = self.request.query_params.get('product_id', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        record_type = self.request.query_params.get('record_type', None)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def in_stock(self, request):
        """入库"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 0))
        warehouse_id = request.data.get('warehouse')
        
        if not product_id or quantity <= 0:
            return Response({'error': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': '产品不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        warehouse = None
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                pass
        
        # 获取当前库存
        last_record = StockRecord.objects.filter(
            product=product, 
            is_deleted=False
        ).order_by('-operate_time').first()
        
        current_balance = last_record.balance if last_record else 0
        
        # 创建入库记录
        record = StockRecord.objects.create(
            product=product,
            warehouse=warehouse,
            record_type='in',
            quantity=quantity,
            balance=current_balance + quantity,
            related_order_no=request.data.get('order_no', ''),
            remark=request.data.get('remark', ''),
            operator=request.user
        )
        
        return Response(StockRecordSerializer(record).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def out_stock(self, request):
        """出库"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 0))
        warehouse_id = request.data.get('warehouse')
        
        if not product_id or quantity <= 0:
            return Response({'error': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': '产品不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        warehouse = None
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                pass
        
        # 获取当前库存
        last_record = StockRecord.objects.filter(
            product=product, 
            is_deleted=False
        ).order_by('-operate_time').first()
        
        current_balance = last_record.balance if last_record else 0
        
        if current_balance < quantity:
            return Response({'error': '库存不足'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建出库记录
        record = StockRecord.objects.create(
            product=product,
            warehouse=warehouse,
            record_type='out',
            quantity=quantity,
            balance=current_balance - quantity,
            related_order_no=request.data.get('order_no', ''),
            remark=request.data.get('remark', ''),
            operator=request.user
        )
        
        return Response(StockRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def query(self, request):
        """库存查询"""
        warehouse_id = request.query_params.get('warehouse')
        product_keyword = request.query_params.get('product', '')
        record_type = request.query_params.get('record_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # 按产品和仓库汇总库存
        from django.db.models import Sum, Q, F, Value
        from django.db.models.functions import Coalesce

        records = StockRecord.objects.filter(is_deleted=False)

        if warehouse_id:
            records = records.filter(warehouse_id=warehouse_id)

        if record_type:
            records = records.filter(record_type=record_type)

        if start_date:
            records = records.filter(operate_time__date__gte=start_date)

        if end_date:
            records = records.filter(operate_time__date__lte=end_date)

        # 如果是查询记录（入库/出库记录）
        if record_type in ['in', 'out']:
            product_id = request.query_params.get('product_id')
            if product_id:
                records = records.filter(product_id=product_id)

            # 分页
            page = int(request.query_params.get('page', 1))
            page_size = 20
            total = records.count()
            records = records.select_related('product', 'operator', 'warehouse').order_by('-operate_time')[(page-1)*page_size:page*page_size]

            return Response({
                'count': total,
                'results': StockRecordSerializer(records, many=True).data
            })

        # 库存汇总查询（按产品和仓库分组）
        result = records.values(
            'product__id', 'product__code', 'product__name',
            'warehouse__id', 'warehouse__name', 'record_type'
        ).annotate(
            total_quantity=Coalesce(Sum('quantity'), 0)
        )

        # 按产品汇总
        from collections import defaultdict
        product_stock = defaultdict(lambda: {'in': 0, 'out': 0, 'warehouses': {}})

        for item in result:
            pid = item['product__id']
            pcode = item['product__code']
            pname = item['product__name']
            wid = item['warehouse__id']
            wname = item['warehouse__name'] or '未指定'
            qty = item['total_quantity']
            rtype = item['record_type']

            if pid not in product_stock:
                product_stock[pid] = {
                    'product_id': pid,
                    'product_code': pcode,
                    'product_name': pname,
                    'in': 0,
                    'out': 0,
                    'quantity': 0,
                    'status': '正常',
                    'warehouses': {}
                }

            if wid:
                if wid not in product_stock[pid]['warehouses']:
                    product_stock[pid]['warehouses'][wid] = {'name': wname, 'in': 0, 'out': 0, 'quantity': 0}

                if rtype == 'in':
                    product_stock[pid]['warehouses'][wid]['in'] += qty
                    product_stock[pid]['warehouses'][wid]['quantity'] += qty
                    product_stock[pid]['in'] += qty
                elif rtype == 'out':
                    product_stock[pid]['warehouses'][wid]['out'] += qty
                    product_stock[pid]['warehouses'][wid]['quantity'] -= qty
                    product_stock[pid]['out'] += qty

            product_stock[pid]['quantity'] = product_stock[pid]['in'] - product_stock[pid]['out']

        # 过滤产品名称/编码
        data = []
        for pid, item in product_stock.items():
            if product_keyword:
                if product_keyword.lower() not in item['product_name'].lower() and \
                   product_keyword.lower() not in item['product_code'].lower():
                    continue

            # 设置状态
            if item['quantity'] <= 0:
                item['status'] = '缺货'
            elif item['quantity'] < 10:
                item['status'] = '库存预警'

            # 仓库名称
            if item['warehouses']:
                item['warehouse_name'] = ', '.join([w['name'] for w in item['warehouses'].values()])
            else:
                item['warehouse_name'] = '-'

            data.append(item)

        return Response(data)


class StockCheckViewSet(viewsets.ModelViewSet):
    """库存盘点视图集"""
    
    queryset = StockCheck.objects.all()
    serializer_class = StockCheckSerializer
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开始盘点"""
        check = self.get_object()
        check.status = 'checking'
        check.start_date = timezone.now().date()
        check.save()
        return Response(StockCheckSerializer(check).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成盘点"""
        check = self.get_object()
        check.status = 'completed'
        check.end_date = timezone.now().date()
        check.save()
        return Response(StockCheckSerializer(check).data)


class WarehouseViewSet(viewsets.ModelViewSet):
    """仓库视图集"""

    queryset = Warehouse.objects.all().order_by('-id')
    serializer_class = WarehouseSerializer


class WarehouseCategoryViewSet(viewsets.ModelViewSet):
    """仓库类别视图集"""

    queryset = WarehouseCategory.objects.all().order_by('sort_order', 'id')
    serializer_class = WarehouseCategorySerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取启用的类别"""
        categories = WarehouseCategory.objects.filter(is_active=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class InventoryTabConfigViewSet(viewsets.ModelViewSet):
    """库存Tab配置视图集"""

    queryset = InventoryTabConfig.objects.all()
    serializer_class = InventoryTabConfigSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    @action(detail=False, methods=['get', 'post'])
    def my_config(self, request):
        """获取或设置当前用户的Tab配置"""
        if request.method == 'GET':
            configs = InventoryTabConfig.objects.filter(user=request.user)
            if not configs.exists():
                # 创建默认配置
                default_tabs = ['overview', 'inbound', 'outbound', 'check', 'report', 'warehouse']
                for i, tab in enumerate(default_tabs):
                    InventoryTabConfig.objects.create(
                        user=request.user,
                        tab_key=tab,
                        is_visible=True,
                        sort_order=i
                    )
                configs = InventoryTabConfig.objects.filter(user=request.user)
            serializer = self.get_serializer(configs, many=True)
            return Response(serializer.data)
        else:
            # 批量更新配置
            configs_data = request.data.get('configs', [])
            for config_data in configs_data:
                InventoryTabConfig.objects.update_or_create(
                    user=request.user,
                    tab_key=config_data.get('tab_key'),
                    defaults={
                        'is_visible': config_data.get('is_visible', True),
                        'sort_order': config_data.get('sort_order', 0)
                    }
                )
            return Response({'status': 'ok'})


@login_required
def inventory_list(request):
    """库存管理页面"""
    # 获取所有产品
    products = Product.objects.filter(is_active=True).select_related('category')

    # 计算统计数据
    total_products = products.count()
    total_stock = sum(p.current_stock for p in products)
    low_stock = sum(1 for p in products if 0 < p.current_stock < p.min_stock)
    out_of_stock = sum(1 for p in products if p.current_stock == 0)

    # 入库记录
    inbound_records = StockRecord.objects.filter(
        record_type='in', is_deleted=False
    ).select_related('product', 'operator', 'warehouse')[:20]

    # 出库记录
    outbound_records = StockRecord.objects.filter(
        record_type='out', is_deleted=False
    ).select_related('product', 'operator', 'warehouse')[:20]

    # 所有记录
    all_records = StockRecord.objects.filter(
        is_deleted=False
    ).select_related('product', 'operator', 'warehouse').order_by('-operate_time')[:50]

    # 盘点记录
    stock_checks = StockCheck.objects.all().select_related('operator')[:20]

    # 期初/期末库存计算 (本月)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 期初库存 = 月初之前的入库 - 出库
    beginning_in = StockRecord.objects.filter(
        record_type='in', operate_time__lt=month_start, is_deleted=False
    ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    beginning_out = StockRecord.objects.filter(
        record_type='out', operate_time__lt=month_start, is_deleted=False
    ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    beginning_stock = beginning_in - beginning_out

    # 本期入库
    total_in = StockRecord.objects.filter(
        record_type='in', operate_time__gte=month_start, is_deleted=False
    ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    # 本期出库
    total_out = StockRecord.objects.filter(
        record_type='out', operate_time__gte=month_start, is_deleted=False
    ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    # 期末库存 = 期初 + 本期入库 - 本期出库
    ending_stock = beginning_stock + total_in - total_out

    # 生成盘点单号
    count = StockCheck.objects.count() + 1
    check_no = "SC{}{:04d}".format(now.strftime('%Y%m%d'), count)

    # 获取所有仓库（用于仓库管理）
    all_warehouses = Warehouse.objects.all()

    # 获取启用的仓库（用于入库/出库选择）
    active_warehouses = Warehouse.objects.filter(is_active=True)

    # 获取所有仓库类别
    warehouse_categories = WarehouseCategory.objects.filter(is_active=True)

    # 按仓库类别统计（动态）
    category_stats = {}
    for cat in warehouse_categories:
        category_stats[cat.code] = {
            'id': cat.id,
            'name': cat.name,
            'code': cat.code,
            'color': cat.color,
            'icon': cat.icon,
            'warehouses': [],
            'total_balance': 0,
            'warehouse_count': 0
        }

    # 按仓库统计库存
    warehouse_stats = []

    for wh in active_warehouses:
        # 该仓库的入库数量
        wh_in = StockRecord.objects.filter(
            warehouse=wh, record_type='in', is_deleted=False
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
        # 该仓库的出库数量
        wh_out = StockRecord.objects.filter(
            warehouse=wh, record_type='out', is_deleted=False
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
        balance = wh_in - wh_out

        # 获取类别信息
        cat_code = wh.category.code if wh.category else None
        cat_name = wh.category.name if wh.category else '-'
        cat_color = wh.category.color if wh.category else '#6c757d'

        wh_stat = {
            'id': wh.id,
            'name': wh.name,
            'category_code': cat_code,
            'category_name': cat_name,
            'category_color': cat_color,
            'in': wh_in,
            'out': wh_out,
            'balance': balance
        }
        warehouse_stats.append(wh_stat)

        # 按类别分组统计
        if cat_code and cat_code in category_stats:
            category_stats[cat_code]['warehouses'].append(wh_stat)
            category_stats[cat_code]['total_balance'] += balance
            category_stats[cat_code]['warehouse_count'] += 1

    # 获取用户Tab配置
    tab_configs = []
    if request.user.is_authenticated:
        tab_configs = InventoryTabConfig.objects.filter(user=request.user).order_by('sort_order')
        if not tab_configs.exists():
            # 创建默认配置
            default_tabs = [
                ('overview', '库存概览', 'bi-speedometer2'),
                ('inbound', '入库', 'bi-box-arrow-in-down'),
                ('outbound', '出库', 'bi-box-arrow-up'),
                ('check', '盘点', 'bi-clipboard-check'),
                ('report', '库存报表', 'bi-file-earmark-bar-graph'),
                ('warehouse', '仓库管理', 'bi-building'),
            ]
            for i, (key, name, icon) in enumerate(default_tabs):
                InventoryTabConfig.objects.create(
                    user=request.user,
                    tab_key=key,
                    is_visible=True,
                    sort_order=i
                )
            tab_configs = InventoryTabConfig.objects.filter(user=request.user).order_by('sort_order')

    context = {
        'products': products,
        'warehouses': all_warehouses,
        'warehouse_stats': warehouse_stats,
        'warehouse_categories': warehouse_categories,
        'category_stats': list(category_stats.values()),
        'tab_configs': tab_configs,
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'inbound_records': inbound_records,
        'outbound_records': outbound_records,
        'all_records': all_records,
        'stock_checks': stock_checks,
        'beginning_stock': beginning_stock,
        'total_in': total_in,
        'total_out': total_out,
        'ending_stock': ending_stock,
        'check_no': check_no,
    }

    return render(request, 'inventory/index.html', context)


@login_required
def warehouse_detail(request, pk):
    """仓库详情页面"""
    try:
        warehouse = Warehouse.objects.get(pk=pk)
    except Warehouse.DoesNotExist:
        return render(request, 'error.html', {'message': '仓库不存在'}, status=404)

    # 仓库统计
    wh_in = StockRecord.objects.filter(
        warehouse=warehouse, record_type='in', is_deleted=False
    ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    wh_out = StockRecord.objects.filter(
        warehouse=warehouse, record_type='out', is_deleted=False
    ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    # 获取该仓库的库存明细
    stock_records = StockRecord.objects.filter(
        warehouse=warehouse, is_deleted=False
    ).select_related('product').order_by('product__code')

    # 按产品汇总
    from collections import defaultdict
    product_summary = defaultdict(lambda: {
        'product_code': '', 'product_name': '', 'category': '', 'in_qty': 0, 'out_qty': 0, 'balance': 0
    })

    for record in stock_records:
        pid = record.product.id
        product_summary[pid]['product_code'] = record.product.code
        product_summary[pid]['product_name'] = record.product.name
        product_summary[pid]['category'] = record.product.category.name if record.product.category else '-'

        if record.record_type == 'in':
            product_summary[pid]['in_qty'] += record.quantity
        elif record.record_type == 'out':
            product_summary[pid]['out_qty'] += record.quantity

        product_summary[pid]['balance'] = product_summary[pid]['in_qty'] - product_summary[pid]['out_qty']

    stock_details = []
    for pid, data in product_summary.items():
        stock_details.append({
            'product_code': data['product_code'],
            'product_name': data['product_name'],
            'category': data['category'],
            'in_qty': data['in_qty'],
            'out_qty': data['out_qty'],
            'balance': data['balance']
        })

    context = {
        'warehouse': warehouse,
        'warehouse_stats': {
            'in': wh_in,
            'out': wh_out,
            'balance': wh_in - wh_out
        },
        'product_count': len(stock_details),
        'stock_details': stock_details
    }

    return render(request, 'inventory/warehouse_detail.html', context)
