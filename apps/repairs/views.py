from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render
from .models import RepairOrder, RepairRecord, RepairPart
from .serializers import RepairOrderSerializer, RepairRecordSerializer, RepairPartSerializer


def repair_list(request):
    """返修管理列表页面"""
    # 获取各状态数量
    stats = {
        'total': RepairOrder.objects.count(),
        'received': RepairOrder.objects.filter(status='received').count(),
        'inbound': RepairOrder.objects.filter(status='inbound').count(),
        'detecting': RepairOrder.objects.filter(status='detecting').count(),
        'quoting': RepairOrder.objects.filter(status='quoting').count(),
        'repairing': RepairOrder.objects.filter(status='repairing').count(),
        'testing': RepairOrder.objects.filter(status='testing').count(),
        'outbound': RepairOrder.objects.filter(status='outbound').count(),
        'completed': RepairOrder.objects.filter(status='completed').count(),
        'cancelled': RepairOrder.objects.filter(status='cancelled').count(),
    }

    # 获取返修单列表
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    repairs = RepairOrder.objects.select_related('customer', 'fault_report').all()

    if status_filter:
        repairs = repairs.filter(status=status_filter)

    if search:
        repairs = repairs.filter(
            Q(repair_no__icontains=search) |
            Q(equipment_sn__icontains=search) |
            Q(equipment_name__icontains=search)
        )

    # 序列化
    serializer = RepairOrderSerializer(repairs, many=True)
    repairs_data = serializer.data

    # 添加状态显示文本
    status_map = dict(RepairOrder.STATUS_CHOICES)
    for repair in repairs_data:
        repair['status_text'] = status_map.get(repair['status'], repair['status'])

    context = {
        'repairs': repairs,
        'stats': stats,
    }
    return render(request, 'repairs/index.html', context)


class RepairOrderViewSet(viewsets.ModelViewSet):
    """返修工单视图集"""
    
    queryset = RepairOrder.objects.all()
    serializer_class = RepairOrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(repair_no__icontains=search) |
                Q(equipment_sn__icontains=search) |
                Q(equipment_name__icontains=search)
            )

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        customer_id = self.request.query_params.get('customer_id', None)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # 添加默认排序
        queryset = queryset.order_by('-id')

        return queryset
    
    @action(detail=True, methods=['post'])
    def inbound(self, request, pk=None):
        """入库"""
        repair = self.get_object()

        # 获取仓库参数
        warehouse_id = request.data.get('warehouse_id')
        if not warehouse_id:
            return Response({'error': '请选择仓库'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.inventory.models import Warehouse, StockRecord

        try:
            warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
        except Warehouse.DoesNotExist:
            return Response({'error': '仓库不存在或已停用'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查设备名称是否已设置
        if not repair.equipment_name:
            return Response({'error': '设备名称为空，无法入库'}, status=status.HTTP_400_BAD_REQUEST)

        # 使用已有的 equipment_name (QuoteProduct) 作为产品
        repair.product = repair.equipment_name

        # 保存仓库信息
        repair.inbound_warehouse = warehouse
        repair.status = 'inbound'
        repair.save()

        # 创建库存记录
        # 获取当前库存
        last_record = StockRecord.objects.filter(
            product=repair.product,
            is_deleted=False
        ).order_by('-operate_time').first()

        current_balance = last_record.balance if last_record else 0

        # 创建入库记录
        StockRecord.objects.create(
            product=repair.product,
            warehouse=warehouse,
            record_type='in',
            quantity=repair.receive_quantity,
            balance=current_balance + repair.receive_quantity,
            related_order_no=repair.repair_no,
            remark=f'返修入库 - {repair.repair_no}',
            operator=request.user
        )

        # 记录操作
        RepairRecord.objects.create(
            repair=repair,
            action='inbound',
            description=f'已入库至仓库: {warehouse.name}',
            operator=request.user
        )

        return Response(RepairOrderSerializer(repair).data)
    
    @action(detail=True, methods=['post'])
    def detect(self, request, pk=None):
        """检测"""
        repair = self.get_object()
        repair.status = 'detecting'
        repair.detect_result = request.data.get('result', '')
        repair.detect_person = request.user
        repair.detect_time = timezone.now()
        repair.save()
        
        RepairRecord.objects.create(
            repair=repair,
            action='detect',
            description=repair.detect_result,
            operator=request.user
        )
        
        return Response(RepairOrderSerializer(repair).data)
    
    @action(detail=True, methods=['post'])
    def quote(self, request, pk=None):
        """报价"""
        repair = self.get_object()
        repair.status = 'quoting'
        repair.quote_amount = request.data.get('quote_amount', 0)
        repair.quote_time = timezone.now()
        repair.save()
        
        RepairRecord.objects.create(
            repair=repair,
            action='quote',
            description=f"报价金额: {repair.quote_amount}",
            operator=request.user
        )
        
        return Response(RepairOrderSerializer(repair).data)
    
    @action(detail=True, methods=['post'])
    def approve_quote(self, request, pk=None):
        """审批报价"""
        repair = self.get_object()
        approved = request.data.get('approved', True)
        
        if approved:
            repair.quote_approved = True
            repair.quote_approver = request.user
            repair.status = 'repairing'
        else:
            repair.status = 'quoting'
        
        repair.save()
        
        RepairRecord.objects.create(
            repair=repair,
            action='quote',
            description=f"报价审批: {'通过' if approved else '拒绝'}",
            operator=request.user
        )
        
        return Response(RepairOrderSerializer(repair).data)
    
    @action(detail=True, methods=['post'])
    def repair(self, request, pk=None):
        """维修"""
        repair = self.get_object()
        repair.status = 'repairing'
        repair.repair_result = request.data.get('result', '')
        repair.repair_person = request.user
        repair.repair_time = timezone.now()
        repair.save()
        
        RepairRecord.objects.create(
            repair=repair,
            action='repair',
            description=repair.repair_result,
            operator=request.user
        )
        
        return Response(RepairOrderSerializer(repair).data)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """质检"""
        repair = self.get_object()
        repair.status = 'testing'
        repair.test_result = request.data.get('result', '')
        repair.test_person = request.user
        repair.test_time = timezone.now()
        repair.save()
        
        RepairRecord.objects.create(
            repair=repair,
            action='test',
            description=f"质检结果: {repair.test_result}",
            operator=request.user
        )
        
        return Response(RepairOrderSerializer(repair).data)
    
    @action(detail=True, methods=['post'])
    def outbound(self, request, pk=None):
        """出库"""
        repair = self.get_object()

        # 检查状态是否允许出库（质检完成或已出库状态）
        if repair.status not in ['testing', 'outbound']:
            return Response({'error': '当前状态不允许出库，请先完成质检'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取出库仓库参数（博乐成品库）
        warehouse_id = request.data.get('warehouse_id')
        if not warehouse_id:
            return Response({'error': '请选择出库仓库'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取出库数量，默认使用接收数量
        outbound_quantity = request.data.get('quantity')
        if outbound_quantity:
            try:
                outbound_quantity = int(outbound_quantity)
                if outbound_quantity <= 0:
                    return Response({'error': '出库数量必须大于0'}, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({'error': '出库数量格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            outbound_quantity = repair.receive_quantity

        from apps.inventory.models import Warehouse, StockRecord

        try:
            outbound_warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
        except Warehouse.DoesNotExist:
            return Response({'error': '出库仓库不存在或已停用'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否有关联产品，如果没有则使用 equipment_name
        if not repair.product:
            if repair.equipment_name:
                repair.product = repair.equipment_name
                repair.save()
            else:
                return Response({'error': '未找到关联产品，无法出库'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否有入库记录
        if not repair.inbound_warehouse:
            return Response({'error': '未找到入库仓库记录，无法出库'}, status=status.HTTP_400_BAD_REQUEST)

        inbound_warehouse = repair.inbound_warehouse
        product = repair.product

        # 获取当前库存（入库仓库）
        last_inbound_record = StockRecord.objects.filter(
            product=product,
            warehouse=inbound_warehouse,
            is_deleted=False
        ).order_by('-operate_time').first()

        inbound_balance = last_inbound_record.balance if last_inbound_record else 0

        if inbound_balance < outbound_quantity:
            return Response({
                'error': f'入库仓库库存不足，当前库存: {inbound_balance}，需要出库: {outbound_quantity}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 从入库仓库出库
        outbound_record = StockRecord.objects.create(
            product=product,
            warehouse=inbound_warehouse,
            record_type='out',
            quantity=outbound_quantity,
            balance=inbound_balance - outbound_quantity,
            related_order_no=repair.repair_no,
            remark=f'返修调拨出库 - {repair.repair_no}',
            operator=request.user
        )

        # 到出库仓库入库
        # 获取出库仓库当前库存
        last_outbound_record = StockRecord.objects.filter(
            product=product,
            warehouse=outbound_warehouse,
            is_deleted=False
        ).order_by('-operate_time').first()

        outbound_warehouse_balance = last_outbound_record.balance if last_outbound_record else 0

        inbound_to_outbound_record = StockRecord.objects.create(
            product=product,
            warehouse=outbound_warehouse,
            record_type='in',
            quantity=outbound_quantity,
            balance=outbound_warehouse_balance + outbound_quantity,
            related_order_no=repair.repair_no,
            remark=f'返修调拨入库 - {repair.repair_no}',
            operator=request.user
        )

        # 保存出库信息
        repair.outbound_warehouse = outbound_warehouse
        repair.outbound_logistics = request.data.get('logistics', '')
        repair.status = 'outbound'
        repair.save()

        # 如果填写了物流单号，创建物流记录
        logistics_no = request.data.get('logistics', '').strip()
        if logistics_no:
            from apps.logistics.models import LogisticsRecord, LogisticsChannel

            # 获取物流渠道（默认使用第一个启用的渠道，或者用户指定的）
            channel_id = request.data.get('logistics_channel_id')
            channel = None
            if channel_id:
                try:
                    channel = LogisticsChannel.objects.get(id=channel_id, is_active=True)
                except LogisticsChannel.DoesNotExist:
                    pass

            if not channel:
                # 如果没有指定渠道，使用默认的第一个可用渠道
                channel = LogisticsChannel.objects.filter(is_active=True).first()

            # 获取客户信息
            receiver_name = ''
            receiver_phone = ''
            receiver_address = ''
            if repair.customer:
                receiver_name = repair.customer.name
                receiver_phone = repair.customer.contact_phone or ''
                receiver_address = repair.customer.address or ''

            # 创建物流记录
            LogisticsRecord.objects.create(
                order_no=repair.repair_no,
                track_no=logistics_no,
                track_type='outbound',  # 发件
                channel=channel,
                sender_name='博乐售后',  # 发货人
                sender_phone='',
                sender_address=inbound_warehouse.address or '',
                receiver_name=receiver_name,
                receiver_phone=receiver_phone,
                receiver_address=receiver_address,
                status='已发货',
                current_location=inbound_warehouse.name
            )

        # 记录操作
        RepairRecord.objects.create(
            repair=repair,
            action='outbound',
            description=f"调拨出库: {inbound_warehouse.name} → {outbound_warehouse.name}, 物流: {repair.outbound_logistics}",
            operator=request.user
        )

        return Response(RepairOrderSerializer(repair).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """维修统计"""
        total = RepairOrder.objects.count()
        pending = RepairOrder.objects.filter(status__in=['received', 'inbound', 'detecting', 'quoting']).count()
        repairing = RepairOrder.objects.filter(status='repairing').count()
        completed = RepairOrder.objects.filter(status='completed').count()
        
        # 平均维修周期
        from django.db.models import Avg, F
        avg_cycle = RepairOrder.objects.filter(
            status='completed',
            repair_time__isnull=False
        ).annotate(
            cycle=F('repair_time') - F('created_at')
        ).aggregate(avg=Avg('cycle'))
        
        return Response({
            'total': total,
            'pending': pending,
            'repairing': repairing,
            'completed': completed,
            'avg_cycle_hours': avg_cycle['avg'].total_seconds() / 3600 if avg_cycle['avg'] else 0,
        })


class RepairRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """维修记录视图集"""
    
    queryset = RepairRecord.objects.all()
    serializer_class = RepairRecordSerializer


class RepairPartViewSet(viewsets.ModelViewSet):
    """维修配件视图集"""
    
    queryset = RepairPart.objects.all()
    serializer_class = RepairPartSerializer
