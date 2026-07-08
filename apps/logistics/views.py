from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import LogisticsChannel, LogisticsRecord, LogisticsTrace
from .serializers import LogisticsChannelSerializer, LogisticsRecordSerializer
import hashlib
import json
import time


class LogisticsChannelViewSet(viewsets.ModelViewSet):
    """物流渠道视图集"""

    queryset = LogisticsChannel.objects.all().order_by('-id')
    serializer_class = LogisticsChannelSerializer


class LogisticsRecordViewSet(viewsets.ModelViewSet):
    """物流记录视图集"""

    queryset = LogisticsRecord.objects.all()
    serializer_class = LogisticsRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        order_no = self.request.query_params.get('order_no', None)
        if order_no:
            queryset = queryset.filter(order_no=order_no)

        track_no = self.request.query_params.get('track_no', None)
        if track_no:
            queryset = queryset.filter(track_no__icontains=track_no)

        track_type = self.request.query_params.get('track_type', None)
        if track_type:
            queryset = queryset.filter(track_type=track_type)

        is_delivered = self.request.query_params.get('is_delivered', None)
        if is_delivered:
            queryset = queryset.filter(is_delivered=is_delivered.lower() == 'true')

        # 添加默认排序
        queryset = queryset.order_by('-id')

        return queryset
    
    @action(detail=True, methods=['post'])
    def query(self, request, pk=None):
        """查询物流信息（腾讯云API）"""
        record = self.get_object()

        # 检查是否可以查询
        if not record.can_query_today():
            if record.is_completed:
                return Response({'error': '该物流单已完成，不再查询'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': '该物流单今天已查询过，每天只能查询一次'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取物流渠道配置
        if not record.channel:
            return Response({'error': '未配置物流渠道'}, status=status.HTTP_400_BAD_REQUEST)

        channel = record.channel

        # 调用查询逻辑
        result = self.query_logistics(record, channel)

        if result.get('success'):
            # 记录查询
            record.record_query()
            return Response({'data': result.get('data'), 'message': '查询成功'})
        else:
            return Response({'error': result.get('error')}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def query_by_track_no(self, request):
        """根据物流单号查询"""
        track_no = request.data.get('track_no')
        if not track_no:
            return Response({'error': '请提供物流单号'}, status=status.HTTP_400_BAD_REQUEST)

        # 查询物流记录
        record = LogisticsRecord.objects.filter(track_no=track_no).first()
        if not record:
            return Response({'error': '未找到物流记录'}, status=status.HTTP_404_NOT_FOUND)

        # 检查是否可以查询
        if not record.can_query_today():
            if record.is_completed:
                return Response({'error': '该物流单已完成，不再查询'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': '该物流单今天已查询过，每天只能查询一次'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取物流渠道配置
        if not record.channel:
            return Response({'error': '未配置物流渠道'}, status=status.HTTP_400_BAD_REQUEST)

        channel = record.channel

        # 调用查询逻辑
        result = self.query_logistics(record, channel)

        if result.get('success'):
            # 记录查询
            record.record_query()
            return Response({'data': result.get('data'), 'message': '查询成功'})
        else:
            return Response({'error': result.get('error')}, status=status.HTTP_400_BAD_REQUEST)

    def query_logistics(self, record, channel):
        """根据不同API类型查询物流"""
        api_type = channel.api_type

        if api_type == 'tencent':
            return self.query_tencent_api(record, channel)
        elif api_type == 'tencent_market':
            return self.query_tencent_market_api(record, channel)
        elif api_type == 'kuaidi':
            return self.query_kuaidi_api(record, channel)
        elif api_type == 'kuaidi100':
            return self.query_kuaidi100_api(record, channel)
        else:
            return {'success': False, 'error': f'暂不支持该API类型: {api_type}'}

    def query_tencent_market_api(self, record, channel):
        """腾讯云市场物流API查询"""
        import requests
        import uuid
        from datetime import datetime

        secret_id = channel.secret_id
        secret_key = channel.secret_key_market
        api_url = channel.market_api_url or 'https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list'

        print(f"\n[腾讯云市场API] 物流单号: {record.track_no}")
        print(f"API配置: SecretID={secret_id[:10]}..., SecretKey={secret_key[:10]}...")
        print(f"API URL: {api_url}")

        if not all([secret_id, secret_key]):
            return {'success': False, 'error': '腾讯云市场API配置不完整，请配置Secret ID和Secret Key'}

        try:
            # 构造签名 - 使用HMAC-SHA1
            datetime_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            sign_str = f"x-date: {datetime_str}"
            
            import hmac
            import hashlib
            import base64
            
            sign = base64.b64encode(hmac.new(secret_key.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha1).digest())
            auth = f'{{"id": "{secret_id}", "x-date": "{datetime_str}", "signature": "{sign.decode("utf-8")}"}}'

            # 请求头
            headers = {
                'request-id': str(uuid.uuid1()),
                'Authorization': auth,
            }

            # 查询参数 - 快递单号和手机号后4位
            query_params = {
                'nu': record.track_no,
            }
            # 如果有收货人电话，取后4位
            if record.receiver_phone and len(record.receiver_phone) >= 4:
                query_params['phone'] = record.receiver_phone[-4:]

            # 拼接URL
            url = api_url
            if query_params:
                import urllib.parse
                url = api_url + '?' + urllib.parse.urlencode(query_params)

            print(f"[请求URL] {url}")
            print(f"[请求头] Authorization: {auth[:50]}...")

            # 发送GET请求
            response = requests.get(url, headers=headers, timeout=15, verify=False)

            print(f"[响应状态码] {response.status_code}")
            print(f"[响应内容] {response.text[:500]}")

            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                
                # 检查成功状态码 - 兼容多种格式
                # showapi_res_code: 0 表示成功
                # showapi_res_body.ret_code: 0 表示成功
                is_success = (
                    result.get('showapi_res_code') == 0 or 
                    result.get('code') == 0 or 
                    result.get('code') == '0'
                )
                
                if is_success:
                    # 从 showapi_res_body 中提取数据
                    body = result.get('showapi_res_body', {})
                    data = body.get('data', [])
                    
                    # 格式化数据以便保存
                    formatted_data = {
                        'status': body.get('status'),
                        'ischeck': body.get('flag'),
                        'data': data,
                        'mailNo': body.get('mailNo'),
                        'updateStr': body.get('updateStr'),
                        'tel': body.get('tel'),
                        'expSpellName': body.get('expSpellName')
                    }
                    
                    self.save_logistics_result(record, formatted_data)
                    return {'success': True, 'data': formatted_data}
                else:
                    error_msg = result.get('showapi_res_error', result.get('message', '查询失败'))
                    return {'success': False, 'error': error_msg}
            else:
                return {'success': False, 'error': f'HTTP错误: {response.status_code}, {response.text[:200]}'}

        except requests.Timeout:
            return {'success': False, 'error': 'API请求超时'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'网络请求失败: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'API调用失败: {str(e)}'}

    def query_tencent_api(self, record, channel):
        """腾讯云物流API查询"""
        import requests

        app_id = channel.app_id
        app_key = channel.app_key
        secret_key = channel.secret_key
        api_url = channel.api_url or 'https://api.express.sdk.tencent.com'

        if not all([app_id, app_key, secret_key]):
            return {'success': False, 'error': '腾讯云API配置不完整，请配置App ID、App Key和Secret Key'}

        # 腾讯云API - 根据快递100的接口格式
        url = f"{api_url}/express/query"

        # 生成签名（腾讯云规范）
        timestamp = str(int(time.time()))
        nonce = str(int(time.time() * 1000))

        # 拼接参数
        params = {
            'app_id': app_id,
            'timestamp': timestamp,
            'nonce': nonce,
            'track_no': record.track_no,
            'order_no': record.order_no
        }

        # 排序并生成签名字符串
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_str = param_str + secret_key

        # 生成签名（MD5）
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

        # 添加签名
        params['sign'] = sign

        try:
            # 发送请求
            response = requests.post(url, data=params, timeout=10)
            response.encoding = 'utf-8'
            result = response.json()

            if result.get('ret') == 0:
                # 查询成功
                data = result.get('data', {})
                # 保存物流状态和轨迹
                self.save_logistics_result(record, data)
                return {'success': True, 'data': data}
            else:
                return {'success': False, 'error': result.get('msg', '查询失败')}
        except requests.Timeout:
            return {'success': False, 'error': 'API请求超时'}
        except Exception as e:
            return {'success': False, 'error': f'API调用失败: {str(e)}'}

    def query_kuaidi100_api(self, record, channel):
        """快递100 API查询"""
        import requests

        api_config = channel.api_config or {}
        app_key = api_config.get('app_key') or channel.app_key

        if not app_key:
            return {'success': False, 'error': '快递100 API Key未配置'}

        url = 'http://www.kuaidi100.com/query'

        try:
            response = requests.post(url, data={
                'app_key': app_key,
                'express_type': 'auto',  # 自动识别
                'text': record.track_no
            }, timeout=10)
            result = response.json()

            if result.get('status') == 200 or result.get('code') == 200:
                data = result.get('data', result)
                self.save_logistics_result(record, data)
                return {'success': True, 'data': data}
            else:
                return {'success': False, 'error': result.get('message', '查询失败')}
        except Exception as e:
            return {'success': False, 'error': f'API调用失败: {str(e)}'}

    def query_kuaidi_api(self, record, channel):
        """快递鸟API查询"""
        import requests

        api_config = channel.api_config or {}
        business_id = api_config.get('business_id') or channel.app_key
        api_key = api_config.get('api_key') or channel.secret_key

        if not all([business_id, api_key]):
            return {'success': False, 'error': '快递鸟API配置不完整'}

        url = 'https://api.kuaidi.com/api/express/query'
        try:
            response = requests.post(url, json={
                'business_id': business_id,
                'apikey': api_key,
                'shipper_code': 'auto',
                'logistics_code': record.track_no,
                'order_code': record.order_no
            }, timeout=10)
            result = response.json()

            if result.get('status') == 200:
                data = result.get('data', {})
                self.save_logistics_result(record, data)
                return {'success': True, 'data': data}
            else:
                return {'success': False, 'error': result.get('message', '查询失败')}
        except Exception as e:
            return {'success': False, 'error': f'API调用失败: {str(e)}'}

    def save_logistics_result(self, record, data):
        """保存物流查询结果"""
        # 更新物流状态
        if isinstance(data, dict):
            # 从返回数据中提取信息
            status = data.get('state', data.get('status', ''))
            current_location = data.get('location', '')
            is_delivered = data.get('ischeck', data.get('is_delivered', False))
            
            # 处理腾讯云市场API返回的状态码 (2=运输中, 3=已签收, 4=异常等)
            status_mapping = {
                0: '已下单',
                1: '已发货',
                2: '运输中',
                3: '已签收',
                4: '异常',
                5: '退件中',
                6: '已退回'
            }
            if isinstance(status, int) and status in status_mapping:
                status = status_mapping[status]
                if status in ['已签收', '已退回']:
                    is_delivered = True
                    is_completed = True
                elif status == '异常':
                    is_completed = False
                else:
                    is_completed = False
            else:
                # 检查是否已完成
                is_completed = status in ['已签收', '已签收', '派送完成', '已取消', '已退回']

            record.status = status
            record.current_location = current_location
            record.is_delivered = is_delivered
            record.is_completed = is_completed

            # 保存物流轨迹
            traces = data.get('data', []) if 'data' in data else data.get('traces', [])
            if isinstance(traces, list):
                for trace in traces:
                    # 兼容不同API返回的字段名
                    trace_time_str = trace.get('time', trace.get('accept_time', trace.get('time_str', trace.get('ftime', ''))))
                    location = trace.get('context', trace.get('location', trace.get('accept_station', trace.get('desc', ''))))
                    status_desc = trace.get('status', trace.get('desc', ''))

                    # 解析时间
                    trace_time = timezone.now()
                    try:
                        if trace_time_str:
                            # 尝试解析不同格式的时间
                            if len(trace_time_str) == 14:  # 20240101123000
                                import datetime
                                trace_time = timezone.make_aware(
                                    datetime.datetime(int(trace_time_str[:4]), int(trace_time_str[4:6]), int(trace_time_str[6:8]), int(trace_time_str[8:10]), int(trace_time_str[10:12])),
                                    timezone.get_current_timezone()
                                )
                            elif trace_time_str.isdigit():
                                trace_time = timezone.datetime.fromtimestamp(int(trace_time_str))
                            else:
                                trace_time = timezone.now()
                    except:
                        trace_time = timezone.now()

                    # 创建或更新轨迹
                    LogisticsTrace.objects.update_or_create(
                        logistics=record,
                        trace_time=trace_time,
                        defaults={
                            'location': location,
                            'status': status_desc,
                            'description': f"{data.get('courier_code', '')} - {data.get('courier_name', '')}"
                        }
                    )

            record.save()
        elif isinstance(data, list) and len(data) > 0:
            # 如果是数组，取第一条
            self.save_logistics_result(record, data[0])
    
    @action(detail=False, methods=['get'])
    def generate_url(self, request):
        """生成公众查询链接"""
        track_no = request.query_params.get('track_no')
        
        if not track_no:
            return Response({'error': '请提供物流单号'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成模拟链接（实际应集成物流API）
        from django.utils import timezone
        from datetime import timedelta

        public_url = f"https://track.example.com/{track_no}"
        expire_time = timezone.now() + timedelta(days=30)

        return Response({
            'public_url': public_url,
            'expire_time': expire_time,
        })


@login_required
def logistics_index(request):
    """物流管理首页"""
    return render(request, 'logistics/index.html')


@login_required
def logistics_channels(request):
    """物流渠道管理页面"""
    return render(request, 'logistics/channels.html')


@login_required
def logistics_unified(request):
    """物流管理统一页面"""
    return render(request, 'logistics/index.html')

