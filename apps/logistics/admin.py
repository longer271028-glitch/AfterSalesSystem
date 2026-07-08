from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import LogisticsChannel, LogisticsRecord, LogisticsTrace


@admin.register(LogisticsChannel)
class LogisticsChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'secret_id', 'market_api_url', 'created_at']
    search_fields = ['name']
    fields = ('name', 'code', 'carrier', 'api_type', 'secret_id', 'secret_key_market', 'market_api_url', ('api_url', 'app_id', 'app_key', 'secret_key'), 'is_active')

    class Media:
        js = ('logistics/js/admin.js',)
        css = {
            'all': ('admin/css/buttons.css',)
        }


@admin.register(LogisticsRecord)
class LogisticsRecordAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'track_no', 'track_type', 'channel', 'status', 'is_delivered', 'query_status', 'query_action', 'created_at']
    list_filter = ['track_type', 'is_delivered', 'is_completed', 'created_at']
    search_fields = ['order_no', 'track_no']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['channel']
    readonly_fields = ['created_at', 'updated_at', 'last_query_time', 'query_count_today', 'query_date']

    def response_add(self, request, obj, post_url_continue=None):
        """添加记录后重定向到物流管理页面"""
        return HttpResponseRedirect('/logistics/')

    def response_change(self, request, obj):
        """修改记录后重定向到物流管理页面"""
        return HttpResponseRedirect('/logistics/')

    def response_delete(self, request, obj_display, obj_id):
        """删除记录后重定向到物流管理页面"""
        return HttpResponseRedirect('/logistics/')

    fields = (
        'order_no', 'track_no', 'track_type', 'channel',
        ('sender_name', 'sender_phone', 'sender_address'),
        ('receiver_name', 'receiver_phone', 'receiver_address'),
        ('status', 'is_delivered', 'is_completed'),
        'current_location', ('public_url', 'is_shared'),
    )

    class Media:
        css = {
            'all': ('admin/css/buttons.css',)
        }

    @admin.display(description='查询状态')
    def query_status(self, obj):
        """显示是否可以查询"""
        if obj.is_completed:
            return mark_safe('<span style="color: gray;">已完成</span>')
        if obj.can_query_today():
            return mark_safe('<span style="color: green;">可查询</span>')
        else:
            return mark_safe(f'<span style="color: red;">今日已查({obj.query_count_today})</span>')

    @admin.display(description='操作')
    def query_action(self, obj):
        """查询操作按钮"""
        if obj.is_completed:
            return mark_safe('<span style="color: #999;">无需查询</span>')
        if obj.can_query_today():
            url = reverse('admin:query_logistics', args=[obj.id])
            return mark_safe(f'<a class="button" href="{url}" onclick="return confirm(\'确定查询该物流信息吗？每天只能查询一次。\')">查询物流</a>')
        else:
            return mark_safe('<span style="color: #999;">今日已查</span>')

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('query/<int:record_id>/', self.admin_site.admin_view(self.query_logistics_view), name='query_logistics'),
        ]
        return custom_urls + urls

    def query_logistics_view(self, request, record_id):
        """查询物流视图"""
        from django.shortcuts import get_object_or_404, redirect, render
        from django.contrib import messages
        import requests
        import hashlib
        import time
        from django.utils import timezone

        print("\n" + "="*80)
        print(f"[开始查询物流] 记录ID: {record_id}")

        record = get_object_or_404(LogisticsRecord, id=record_id)

        print(f"[物流记录] 单号: {record.track_no}, 类型: {record.track_type}, 当前状态: {record.status}")
        print(f"[查询限制] 是否可查询: {record.can_query_today()}, 今日查询次数: {record.query_count_today}")

        # 检查是否可以查询
        if not record.can_query_today():
            print("[拒绝查询] 今天已查询过或物流已完成")
            messages.error(request, '该物流单今天已查询过，请明天再试')
            return redirect('/admin/logistics/logisticsrecord/')

        # 获取物流渠道配置
        if not record.channel:
            print("[错误] 未配置物流渠道")
            messages.error(request, '未配置物流渠道')
            return redirect('/admin/logistics/logisticsrecord/')

        channel = record.channel
        api_type = channel.api_type

        print(f"[物流渠道] 名称: {channel.name}, 类型: {api_type}")

        # 根据API类型查询
        if api_type == 'tencent_market':
            print("使用腾讯云市场API查询...")
            result = self._query_tencent_market(record, channel)
        elif api_type == 'tencent':
            print("使用腾讯云API查询...")
            result = self._query_tencent(record, channel)
        elif api_type == 'kuaidi100':
            print("使用快递100 API查询...")
            result = self._query_kuaidi100(record, channel)
        elif api_type == 'kuaidi':
            print("使用快递鸟API查询...")
            result = self._query_kuaidi(record, channel)
        else:
            print(f"[错误] 暂不支持该API类型: {api_type}")
            result = {'success': False, 'error': f'暂不支持该API类型: {api_type}'}

        if result.get('success'):
            # 记录查询
            record.record_query()
            print(f"[记录查询] 查询时间已更新，状态: {record.status}")
            messages.success(request, f'查询成功！物流状态：{record.status}')

            # 获取物流轨迹
            traces = record.traces.all().order_by('-trace_time')
            print(f"[物流轨迹] 共 {traces.count()} 条")

            # 渲染查询结果页面
            context = {
                'record': record,
                'traces': traces,
                'has_permission': True,
                'opts': self.model._meta,
                'title': f'物流查询结果 - {record.track_no}',
                'is_popup': False,
                'is_nav_sidebar_enabled': True,
            }
            print("[渲染查询结果页面]")
            print("="*80 + "\n")
            return render(request, 'admin/logistics/query_result.html', context)
        else:
            print(f"[查询失败] {result.get('error', '未知错误')}")
            messages.error(request, f'查询失败：{result.get("error", "未知错误")}')

        print("[重定向回列表页]")
        print("="*80 + "\n")
        return redirect('/admin/logistics/logisticsrecord/')

    def _query_tencent_market(self, record, channel):
        """腾讯云市场API查询"""
        import requests
        import hmac
        import hashlib
        import base64
        import time
        import json

        secret_id = channel.secret_id
        secret_key = channel.secret_key_market
        api_url = channel.market_api_url or 'https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list'

        print("\n" + "="*80)
        print(f"[腾讯云市场API查询] 物流单号: {record.track_no}")
        print(f"API配置: Secret ID={secret_id[:10]}...*, Secret Key={secret_key[:10]}...*")
        print(f"API URL: {api_url}")

        if not all([secret_id, secret_key]):
            print("[错误] 腾讯云市场API配置不完整")
            return {'success': False, 'error': '腾讯云市场API配置不完整，请配置Secret ID和Secret Key'}

        try:
            # 构造请求参数
            timestamp = str(int(time.time()))
            nonce = str(int(time.time() * 1000))

            params = {
                'logistics_no': record.track_no,  # 物流单号
                'order_no': record.order_no,       # 订单号（可选）
                'timestamp': timestamp,
                'nonce': nonce
            }

            print(f"[请求参数] {params}")

            # 生成签名
            # 腾讯云市场API签名算法：HMAC-SHA256(secretKey, 参数字符串)
            # 参数字符串：按字母顺序排序，格式 key1=value1&key2=value2
            sorted_params = sorted(params.items())
            sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])

            print(f"[签名字符串] {sign_str}")

            # 使用HMAC-SHA256生成签名
            signature = hmac.new(
                secret_key.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            print(f"[签名] {signature}")

            # 设置请求头
            headers = {
                'Content-Type': 'application/json',
                'X-Auth-Code': f'{secret_id}:{signature}',
                'X-Timestamp': timestamp,
                'X-Nonce': nonce
            }

            print(f"[请求头] Content-Type: application/json")
            print(f"[请求头] X-Auth-Code: {secret_id[:10]}...*:{signature[:20]}...")

            # 发送POST请求
            print(f"[请求URL] {api_url}")
            print(f"[请求方法] POST")
            print(f"[请求体] {json.dumps(params, ensure_ascii=False)}")

            response = requests.post(api_url, json=params, headers=headers, timeout=10)

            print(f"[响应状态码] {response.status_code}")
            print(f"[响应头] Content-Type: {response.headers.get('Content-Type', 'unknown')}")

            # 解析响应
            result = response.json()
            print(f"[响应内容] {json.dumps(result, ensure_ascii=False, indent=2)}")

            # 检查响应状态
            if response.status_code == 200 and result.get('code') == 0:
                # 查询成功
                data = result.get('data', {})
                self._save_logistics_result(record, data)
                print("[查询成功] 物流状态和轨迹已保存")
                return {'success': True, 'data': data}
            else:
                error_msg = result.get('message', result.get('msg', '查询失败'))
                print(f"[查询失败] {error_msg}")
                return {'success': False, 'error': error_msg}

        except requests.Timeout:
            print("[错误] API请求超时")
            return {'success': False, 'error': 'API请求超时'}
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'网络请求失败: {str(e)}'}
        except json.JSONDecodeError as e:
            print(f"[错误] 响应解析失败: {str(e)}")
            print(f"[响应原文] {response.text}")
            return {'success': False, 'error': f'响应解析失败: {str(e)}'}
        except Exception as e:
            print(f"[错误] API调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'API调用失败: {str(e)}'}
        finally:
            print("="*80 + "\n")

    def _query_tencent(self, record, channel):
        """腾讯云物流API查询"""
        import requests
        import hashlib
        import time

        app_id = channel.app_id
        app_key = channel.app_key
        secret_key = channel.secret_key
        api_url = channel.api_url or 'https://api.express.sdk.tencent.com'

        print("\n" + "="*80)
        print(f"[腾讯云API查询] 物流单号: {record.track_no}")
        print(f"API配置: App ID={app_id}, App Key={app_key[:10]}...*, Secret Key={secret_key[:10]}...*")
        print(f"API URL: {api_url}")

        if not all([app_id, app_key, secret_key]):
            print("[错误] 腾讯云API配置不完整")
            return {'success': False, 'error': '腾讯云API配置不完整，请配置App ID、App Key和Secret Key'}

        try:
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

            print(f"[请求参数] {params}")
            print(f"[签名字符串] {sign_str[:50]}... (前50字符)")

            # 发送请求
            url = f"{api_url}/express/query"
            print(f"[请求URL] {url}")
            print(f"[请求方法] POST")

            response = requests.post(url, data=params, timeout=10)

            print(f"[响应状态码] {response.status_code}")
            print(f"[响应头] Content-Type: {response.headers.get('Content-Type', 'unknown')}")

            response.encoding = 'utf-8'
            result = response.json()

            print(f"[响应内容] {result}")

            if result.get('ret') == 0:
                # 查询成功，保存物流状态和轨迹
                self._save_logistics_result(record, result.get('data', {}))
                print("[查询成功] 物流状态和轨迹已保存")
                return {'success': True, 'data': result.get('data', {})}
            else:
                print(f"[查询失败] {result.get('msg', '查询失败')}")
                return {'success': False, 'error': result.get('msg', '查询失败')}
        except requests.Timeout:
            print("[错误] API请求超时")
            return {'success': False, 'error': 'API请求超时'}
        except Exception as e:
            print(f"[错误] API调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'API调用失败: {str(e)}'}
        finally:
            print("="*80 + "\n")

    def _query_kuaidi100(self, record, channel):
        """快递100 API查询"""
        import requests

        api_config = channel.api_config or {}
        app_key = api_config.get('app_key') or channel.app_key

        print("\n" + "="*80)
        print(f"[快递100 API查询] 物流单号: {record.track_no}")
        print(f"API Key: {app_key[:10]}...*")

        if not app_key:
            print("[错误] 快递100 API Key未配置")
            return {'success': False, 'error': '快递100 API Key未配置'}

        try:
            url = 'https://www.kuaidi100.com/query'
            print(f"[请求URL] {url}")
            print(f"[请求参数] app_key={app_key}, express_type=auto, text={record.track_no}")

            response = requests.post(url, data={
                'app_key': app_key,
                'express_type': 'auto',  # 自动识别
                'text': record.track_no
            }, timeout=10)

            print(f"[响应状态码] {response.status_code}")

            result = response.json()
            print(f"[响应内容] {result}")

            if result.get('status') == 200 or result.get('code') == 200:
                data = result.get('data', result)
                self._save_logistics_result(record, data)
                print("[查询成功] 物流状态和轨迹已保存")
                return {'success': True, 'data': data}
            else:
                print(f"[查询失败] {result.get('message', '查询失败')}")
                return {'success': False, 'error': result.get('message', '查询失败')}
        except Exception as e:
            print(f"[错误] API调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'API调用失败: {str(e)}'}
        finally:
            print("="*80 + "\n")

    def _query_kuaidi(self, record, channel):
        """快递鸟API查询"""
        import requests

        api_config = channel.api_config or {}
        business_id = api_config.get('business_id') or channel.app_key
        api_key = api_config.get('api_key') or channel.secret_key

        print("\n" + "="*80)
        print(f"[快递鸟API查询] 物流单号: {record.track_no}")
        print(f"API配置: Business ID={business_id}, API Key={api_key[:10]}...*")

        if not all([business_id, api_key]):
            print("[错误] 快递鸟API配置不完整")
            return {'success': False, 'error': '快递鸟API配置不完整'}

        try:
            url = 'https://api.kuaidi.com/api/express/query'
            payload = {
                'business_id': business_id,
                'apikey': api_key,
                'shipper_code': 'auto',
                'logistics_code': record.track_no,
                'order_code': record.order_no
            }

            print(f"[请求URL] {url}")
            print(f"[请求参数] {payload}")

            response = requests.post(url, json=payload, timeout=10)

            print(f"[响应状态码] {response.status_code}")

            result = response.json()
            print(f"[响应内容] {result}")

            if result.get('status') == 200:
                data = result.get('data', {})
                self._save_logistics_result(record, data)
                print("[查询成功] 物流状态和轨迹已保存")
                return {'success': True, 'data': data}
            else:
                print(f"[查询失败] {result.get('message', '查询失败')}")
                return {'success': False, 'error': result.get('message', '查询失败')}
        except Exception as e:
            print(f"[错误] API调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'API调用失败: {str(e)}'}
        finally:
            print("="*80 + "\n")

    def _save_logistics_result(self, record, data):
        """保存物流查询结果"""
        from django.utils import timezone
        from .models import LogisticsTrace
        import datetime

        print("\n[保存物流结果] 开始处理...")

        # 更新物流状态
        if isinstance(data, dict):
            # 从返回数据中提取信息
            status = data.get('state', data.get('status', ''))
            current_location = data.get('location', '')
            is_delivered = data.get('ischeck', data.get('is_delivered', False))

            # 检查是否已完成
            is_completed = status in ['已签收', '派送完成', '已取消', '已退回']

            print(f"[解析状态] 物流状态: {status}, 是否已签收: {is_delivered}, 是否已完成: {is_completed}")
            print(f"[当前位置] {current_location}")

            record.status = status
            record.current_location = current_location
            record.is_delivered = is_delivered
            record.is_completed = is_completed

            # 保存物流轨迹
            traces = data.get('data', []) if 'data' in data else data.get('traces', [])
            print(f"[物流轨迹] 共 {len(traces) if isinstance(traces, list) else 0} 条")

            if isinstance(traces, list):
                saved_count = 0
                for trace in traces:
                    trace_time_str = trace.get('time', trace.get('accept_time', trace.get('time_str', '')))
                    location = trace.get('context', trace.get('location', trace.get('accept_station', '')))
                    status_desc = trace.get('status', trace.get('desc', ''))

                    # 解析时间
                    trace_time = timezone.now()
                    try:
                        if trace_time_str:
                            # 尝试解析不同格式的时间
                            if len(trace_time_str) == 14:  # 20240101123000
                                trace_time = timezone.make_aware(
                                    datetime.datetime(int(trace_time_str[:4]), int(trace_time_str[4:6]), int(trace_time_str[6:8]),
                                                      int(trace_time_str[8:10]), int(trace_time_str[10:12])),
                                    timezone.get_current_timezone()
                                )
                            elif trace_time_str.isdigit() and len(trace_time_str) > 10:
                                trace_time = timezone.datetime.fromtimestamp(int(trace_time_str))
                    except:
                        trace_time = timezone.now()

                    # 创建或更新轨迹
                    trace_obj, created = LogisticsTrace.objects.get_or_create(
                        logistics=record,
                        trace_time=trace_time,
                        defaults={
                            'location': location,
                            'status': status_desc,
                            'description': f"{data.get('courier_code', '')} - {data.get('courier_name', '')}"
                        }
                    )
                    if created:
                        saved_count += 1

                print(f"[保存轨迹] 新增 {saved_count} 条，跳过已存在的 {len(traces) - saved_count} 条")

            record.save()
            print("[保存成功] 物流记录已更新")
        elif isinstance(data, list) and len(data) > 0:
            # 如果是数组，取第一条
            print("[处理数组格式] 取第一条数据")
            self._save_logistics_result(record, data[0])
        else:
            print(f"[警告] 无法识别的数据格式: {type(data)}")


@admin.register(LogisticsTrace)
class LogisticsTraceAdmin(admin.ModelAdmin):
    list_display = ['logistics', 'trace_time', 'location', 'status']
    list_filter = ['trace_time']
    date_hierarchy = 'trace_time'
    raw_id_fields = ['logistics']
