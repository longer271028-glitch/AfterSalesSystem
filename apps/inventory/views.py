from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .models import StockRecord, StockCheck, StockCheckDetail, Warehouse, WarehouseCategory, InventoryTabConfig
from .constants import STOCK_OUT_THRESHOLD, STOCK_LOW_THRESHOLD
from apps.quotes.models import QuoteProduct
from apps.quotes.serializers import QuoteProductSerializer
from .serializers import (
    StockRecordSerializer, StockCheckSerializer, WarehouseSerializer,
    WarehouseCategorySerializer, InventoryTabConfigSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """产品视图集 - 使用QuoteProduct"""

    queryset = QuoteProduct.objects.filter(status='active').order_by('-created_at')
    serializer_class = QuoteProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
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
            # 获取库存不足的产品
            from django.db.models import Sum
            product_ids = StockRecord.objects.filter(
                is_deleted=False
            ).values('product_id').annotate(
                balance=F('balance')
            ).filter(
                balance__lt=10
            ).values_list('product_id', flat=True)
            queryset = queryset.filter(id__in=product_ids)

        return queryset


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
            product = QuoteProduct.objects.get(id=product_id)
        except QuoteProduct.DoesNotExist:
            return Response({'error': '产品不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        warehouse = None
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                return Response({'error': '仓库不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取当前库存（按仓库查询）
        last_record = StockRecord.objects.filter(
            product=product, 
            warehouse=warehouse,
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
        """出库/调拨"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 0))
        out_warehouse_id = request.data.get('out_warehouse')  # 出库仓库
        in_warehouse_id = request.data.get('in_warehouse')    # 入库仓库

        if not product_id or quantity <= 0:
            return Response({'error': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = QuoteProduct.objects.get(id=product_id)
        except QuoteProduct.DoesNotExist:
            return Response({'error': '产品不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取出库仓库
        out_warehouse = None
        if out_warehouse_id:
            try:
                out_warehouse = Warehouse.objects.get(id=out_warehouse_id)
            except Warehouse.DoesNotExist:
                return Response({'error': '出库仓库不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取入库仓库
        in_warehouse = None
        if in_warehouse_id:
            try:
                in_warehouse = Warehouse.objects.get(id=in_warehouse_id)
            except Warehouse.DoesNotExist:
                return Response({'error': '入库仓库不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 如果出库仓库和入库仓库相同，则为普通出库
        if out_warehouse and in_warehouse and out_warehouse.id == in_warehouse.id:
            # 普通出库
            last_record = StockRecord.objects.filter(
                product=product, 
                warehouse=out_warehouse,
                is_deleted=False
            ).order_by('-operate_time').first()
            
            current_balance = last_record.balance if last_record else 0
            
            if current_balance < quantity:
                return Response({'error': '库存不足'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建出库记录
            record = StockRecord.objects.create(
                product=product,
                warehouse=out_warehouse,
                record_type='out',
                quantity=quantity,
                balance=current_balance - quantity,
                related_order_no=request.data.get('order_no', ''),
                remark=request.data.get('remark', ''),
                operator=request.user
            )
            return Response(StockRecordSerializer(record).data, status=status.HTTP_201_CREATED)
        
        # 调拨模式：出库仓库减少，入库仓库增加
        # 1. 处理出库
        out_record = None
        if out_warehouse:
            last_record = StockRecord.objects.filter(
                product=product, 
                warehouse=out_warehouse,
                is_deleted=False
            ).order_by('-operate_time').first()
            
            current_balance = last_record.balance if last_record else 0
            
            if current_balance < quantity:
                return Response({'error': f'出库仓库库存不足 (当前: {current_balance})'}, status=status.HTTP_400_BAD_REQUEST)
            
            out_record = StockRecord.objects.create(
                product=product,
                warehouse=out_warehouse,
                record_type='out',
                quantity=quantity,
                balance=current_balance - quantity,
                related_order_no=request.data.get('order_no', ''),
                remark=f"调拨出库至: {in_warehouse.name if in_warehouse else '未知'}",
                operator=request.user
            )
        
        # 2. 处理入库
        in_record = None
        if in_warehouse:
            last_record = StockRecord.objects.filter(
                product=product, 
                warehouse=in_warehouse,
                is_deleted=False
            ).order_by('-operate_time').first()
            
            current_balance = last_record.balance if last_record else 0
            
            in_record = StockRecord.objects.create(
                product=product,
                warehouse=in_warehouse,
                record_type='in',
                quantity=quantity,
                balance=current_balance + quantity,
                related_order_no=request.data.get('order_no', ''),
                remark=f"调拨入库自: {out_warehouse.name if out_warehouse else '未知'}",
                operator=request.user
            )
        
        return Response({
            'out_record': StockRecordSerializer(out_record).data if out_record else None,
            'in_record': StockRecordSerializer(in_record).data if in_record else None,
            'message': '调拨成功'
        }, status=status.HTTP_201_CREATED)

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
            'product__id', 'product__name',
            'warehouse__id', 'warehouse__name', 'record_type'
        ).annotate(
            total_quantity=Coalesce(Sum('quantity'), 0)
        )

        # 按产品汇总
        from collections import defaultdict
        product_stock = defaultdict(lambda: {'in': 0, 'out': 0, 'warehouses': {}})

        for item in result:
            pid = item['product__id']
            pname = item['product__name']
            wid = item['warehouse__id']
            wname = item['warehouse__name'] or '未指定'
            qty = item['total_quantity']
            rtype = item['record_type']

            if pid not in product_stock:
                product_stock[pid] = {
                    'product_id': pid,
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
                if product_keyword.lower() not in item['product_name'].lower():
                    continue

            # 设置状态
            if item['quantity'] <= STOCK_OUT_THRESHOLD:
                item['status'] = '缺货'
            elif item['quantity'] < STOCK_LOW_THRESHOLD:
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
        """开始盘点 - 自动获取当前库存数据"""
        check = self.get_object()
        if check.status != 'draft':
            return Response({'error': '只有草稿状态的盘点单才能开始'}, status=status.HTTP_400_BAD_REQUEST)

        check.status = 'checking'
        check.start_date = timezone.now().date()

        # 自动获取该仓库的所有产品库存作为账面数量
        from apps.quotes.models import QuoteProduct

        warehouse_name = check.warehouse
        # 获取该仓库的所有库存记录（warehouse是外键，直接用name过滤）
        stock_records = StockRecord.objects.filter(
            warehouse__name=warehouse_name,
            is_deleted=False
        ).values('product_id').annotate(
            total_in=models.Sum('quantity', filter=models.Q(record_type='in')),
            total_out=models.Sum('quantity', filter=models.Q(record_type='out'))
        )

        # 创建盘点明细
        details_created = 0
        for record in stock_records:
            if record['total_in'] or record['total_out']:
                book_qty = (record['total_in'] or 0) - (record['total_out'] or 0)
                if book_qty >= 0:  # 显示所有有库存的产品（包括0）
                    try:
                        product = QuoteProduct.objects.get(id=record['product_id'])
                        StockCheckDetail.objects.create(
                            check_record=check,
                            product=product,
                            book_quantity=book_qty,
                            actual_quantity=book_qty,  # 初始值与账面相同
                            difference=0
                        )
                        details_created += 1
                    except QuoteProduct.DoesNotExist:
                        pass

        check.save()
        return Response({
            'data': StockCheckSerializer(check).data,
            'message': f'已开始盘点，自动导入{details_created}种产品的库存数据'
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成盘点"""
        check = self.get_object()
        if check.status != 'checking':
            return Response({'error': '只有盘点中的单据才能完成'}, status=status.HTTP_400_BAD_REQUEST)

        # 计算盘点结果
        details = check.details.all()
        total_book = sum(d.book_quantity for d in details)
        total_actual = sum(d.actual_quantity for d in details)
        total_diff = sum(d.difference for d in details)

        check.status = 'completed'
        check.end_date = timezone.now().date()
        check.remark = f"账面数量:{total_book}, 实际数量:{total_actual}, 差异:{total_diff}"
        check.save()

        return Response({
            'data': StockCheckSerializer(check).data,
            'summary': {
                'total_products': details.count(),
                'total_book': total_book,
                'total_actual': total_actual,
                'total_difference': total_diff
            }
        })

    @action(detail=True, methods=['post'])
    def update_detail(self, request, pk=None):
        """更新盘点明细 - 修正数据"""
        check = self.get_object()
        if check.status != 'checking':
            return Response({'error': '只有盘点中的单据才能修正'}, status=status.HTTP_400_BAD_REQUEST)

        detail_id = request.data.get('detail_id')
        actual_quantity = request.data.get('actual_quantity')

        if not detail_id or actual_quantity is None:
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            detail = check.details.get(id=detail_id)
            detail.actual_quantity = int(actual_quantity)
            detail.difference = detail.actual_quantity - detail.book_quantity
            if request.data.get('remark'):
                detail.remark = request.data.get('remark')
            detail.save()

            return Response(StockCheckDetailSerializer(detail).data)
        except StockCheckDetail.DoesNotExist:
            return Response({'error': '盘点明细不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def batch_update(self, request, pk=None):
        """批量更新盘点明细"""
        check = self.get_object()
        if check.status != 'checking':
            return Response({'error': '只有盘点中的单据才能修正'}, status=status.HTTP_400_BAD_REQUEST)

        updates = request.data.get('updates', [])
        updated_count = 0

        for update in updates:
            detail_id = update.get('detail_id')
            actual_quantity = update.get('actual_quantity')
            if detail_id and actual_quantity is not None:
                try:
                    detail = check.details.get(id=detail_id)
                    detail.actual_quantity = int(actual_quantity)
                    detail.difference = detail.actual_quantity - detail.book_quantity
                    detail.save()
                    updated_count += 1
                except StockCheckDetail.DoesNotExist:
                    pass

        return Response({'message': f'已更新{updated_count}条记录'})

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """获取盘点报告"""
        check = self.get_object()
        details = check.details.all()

        # 分类统计
        normal_count = details.filter(difference=0).count()
        profit_count = details.filter(difference__gt=0).count()  # 盘盈
        loss_count = details.filter(difference__lt=0).count()    # 盘亏

        total_book = sum(d.book_quantity for d in details)
        total_actual = sum(d.actual_quantity for d in details)
        total_diff = sum(d.difference for d in details)

        return Response({
            'check_no': check.check_no,
            'warehouse': check.warehouse,
            'status': check.status,
            'start_date': check.start_date,
            'end_date': check.end_date,
            'summary': {
                'total_products': details.count(),
                'normal_count': normal_count,
                'profit_count': profit_count,
                'loss_count': loss_count,
                'total_book': total_book,
                'total_actual': total_actual,
                'total_difference': total_diff
            },
            'details': StockCheckDetailSerializer(details, many=True).data
        })


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
    # 获取所有产品 - 使用QuoteProduct
    products = QuoteProduct.objects.filter(status='active').select_related('series')

    # 计算统计数据
    total_products = products.count()
    # 计算每个产品的库存
    total_stock = 0
    low_stock = 0
    out_of_stock = 0

    for product in products:
        product_stock = 0
        # 获取该产品的最新库存记录
        latest_record = StockRecord.objects.filter(
            product=product, is_deleted=False
        ).order_by('-operate_time').first()
        if latest_record:
            product_stock = latest_record.balance

        total_stock += product_stock
        if product_stock <= STOCK_OUT_THRESHOLD:
            out_of_stock += 1
        elif product_stock < STOCK_LOW_THRESHOLD:
            low_stock += 1

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

    # 当前时间（用于报表筛选）
    now = timezone.now()

    # 获取报表筛选参数
    report_month = request.GET.get('month', now.strftime('%Y-%m'))
    filter_warehouse = request.GET.get('warehouse', '')
    filter_type = request.GET.get('type', '')

    # 解析月份
    try:
        year, month = map(int, report_month.split('-'))
        month_start = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            month_end = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            month_end = timezone.make_aware(datetime(year, month + 1, 1))
    except:
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

    # 期初/期末库存计算 (按筛选月份)
    beginning_qs = StockRecord.objects.filter(
        record_type='in', operate_time__lt=month_start, is_deleted=False
    )
    beginning_out_qs = StockRecord.objects.filter(
        record_type='out', operate_time__lt=month_start, is_deleted=False
    )

    # 按仓库筛选
    if filter_warehouse:
        beginning_qs = beginning_qs.filter(warehouse__name=filter_warehouse)
        beginning_out_qs = beginning_out_qs.filter(warehouse__name=filter_warehouse)

    beginning_in = beginning_qs.aggregate(total=Coalesce(Sum('quantity'), 0))['total']
    beginning_out = beginning_out_qs.aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    beginning_stock = beginning_in - beginning_out

    # 本期入库
    in_qs = StockRecord.objects.filter(
        record_type='in', operate_time__gte=month_start, operate_time__lt=month_end, is_deleted=False
    )
    # 本期出库
    out_qs = StockRecord.objects.filter(
        record_type='out', operate_time__gte=month_start, operate_time__lt=month_end, is_deleted=False
    )

    # 按仓库筛选
    if filter_warehouse:
        in_qs = in_qs.filter(warehouse__name=filter_warehouse)
        out_qs = out_qs.filter(warehouse__name=filter_warehouse)

    total_in = in_qs.aggregate(total=Coalesce(Sum('quantity'), 0))['total']
    total_out = out_qs.aggregate(total=Coalesce(Sum('quantity'), 0))['total']

    # 期末库存 = 期初 + 本期入库 - 本期出库
    ending_stock = beginning_stock + total_in - total_out

    # 重新查询筛选后的记录
    all_records_qs = StockRecord.objects.filter(is_deleted=False)

    # 按仓库筛选
    if filter_warehouse:
        all_records_qs = all_records_qs.filter(warehouse__name=filter_warehouse)

    # 按类型筛选
    if filter_type:
        all_records_qs = all_records_qs.filter(record_type=filter_type)

    # 按月份筛选
    all_records_qs = all_records_qs.filter(
        operate_time__gte=month_start,
        operate_time__lt=month_end
    )

    all_records = all_records_qs.select_related('product', 'operator', 'warehouse').order_by('-operate_time')[:50]

    # 生成盘点单号
    count = StockCheck.objects.count() + 1
    check_no = "SC{}{:04d}".format(now.strftime('%Y%m%d'), count)

    # 获取所有仓库（用于仓库管理）
    all_warehouses = Warehouse.objects.select_related('manager', 'category').all()

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
        'report_month': report_month,
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
    ).select_related('product').order_by('product__name')

    # 按产品汇总 - 使用最新记录的余额
    from collections import defaultdict
    product_summary = defaultdict(lambda: {
        'product_name': '', 'series': '', 'in_qty': 0, 'out_qty': 0, 'balance': 0
    })

    # 先按产品分组，获取每个产品的最新余额
    latest_balances = {}
    for record in stock_records:
        pid = record.product.id
        if pid not in latest_balances:
            latest_balances[pid] = record.balance
        # 始终更新为最新的
        latest_balances[pid] = record.balance

    # 重新遍历计算入库/出库总量
    for record in stock_records:
        pid = record.product.id
        product_summary[pid]['product_name'] = record.product.name
        product_summary[pid]['series'] = record.product.series.name if record.product.series else '-'

        if record.record_type == 'in':
            product_summary[pid]['in_qty'] += record.quantity
        elif record.record_type == 'out':
            product_summary[pid]['out_qty'] += record.quantity

        # 使用最新记录的余额
        product_summary[pid]['balance'] = latest_balances.get(pid, 0)

    stock_details = []
    for pid, data in product_summary.items():
        stock_details.append({
            'product_name': data['product_name'],
            'series': data['series'],
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
