import json
import time
import datetime
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# --- دالة مساعدة لتوليد تاريخ افتراضي للبيانات الأولية ---
def get_next_work_day():
    d = datetime.date.today() + datetime.timedelta(days=1)
    # تخطي الجمعة (4) والسبت (5)
    while d.weekday() in [4, 5]: 
        d += datetime.timedelta(days=1)
    return d.isoformat()

# --- قاعدة بيانات مبسطة (في الذاكرة) مبنية بلغة بايثون ---
bookings = [
    {
        "id": 1,
        "hall": "القاعة الكبيرة",
        "date": get_next_work_day(),
        "time": "09:00 - 10:00",
        "department": "قسم التمريض",
        "title": "دورة تدريبية: مكافحة العدوى",
        "lecturer": "د. أحمد",
        "requester": "فاطمة - تحويلة 102",
        "status": "approved"
    },
    {
        "id": 2,
        "hall": "القاعة الزجاجية",
        "date": get_next_work_day(),
        "time": "11:00 - 12:00",
        "department": "الإدارة الطبية",
        "title": "الاجتماع الأسبوعي",
        "lecturer": "",
        "requester": "محمد - تحويلة 505",
        "status": "pending"
    }
]

# --- واجهة المستخدم (نفس التصميم تماماً مدمج كمتغير نصي) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام حجز القاعات - مستشفى الرعاية المديدة</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Cairo', 'sans-serif'] },
                    colors: {
                        medical: { 50: '#f0fdfa', 100: '#ccfbf1', 500: '#14b8a6', 600: '#0d9488', 700: '#0f766e', 900: '#134e4a' }
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #f8fafc; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        .fade-in { animation: fadeIn 0.3s ease-in-out; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="text-gray-800 antialiased font-sans">

    <!-- Navbar -->
    <nav class="bg-medical-700 text-white shadow-lg relative z-10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-hospital text-2xl"></i>
                    <div>
                        <h1 class="font-bold text-lg leading-tight">مستشفى الرعاية المديدة بالظهران</h1>
                        <p class="text-medical-100 text-xs">نظام إدارة وحجز القاعات (نسخة بايثون)</p>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row gap-6">
        
        <!-- Sidebar Navigation -->
        <aside class="w-full md:w-64 flex-shrink-0">
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden sticky top-4">
                <button onclick="switchTab('booking-form')" id="btn-booking-form" class="w-full flex items-center gap-3 px-5 py-4 text-right transition-colors border-b border-gray-50 bg-medical-50 text-medical-700 font-semibold cursor-pointer">
                    <i class="fa-solid fa-calendar-plus w-5 text-center"></i>
                    <span>طلب حجز جديد</span>
                </button>
                <button onclick="switchTab('schedule-view')" id="btn-schedule-view" class="w-full flex items-center gap-3 px-5 py-4 text-right transition-colors border-b border-gray-50 hover:bg-gray-50 text-gray-600 cursor-pointer">
                    <i class="fa-solid fa-table-list w-5 text-center"></i>
                    <span>جدول القاعات</span>
                </button>
                <button onclick="switchTab('admin-view')" id="btn-admin-view" class="w-full flex items-center gap-3 px-5 py-4 text-right transition-colors hover:bg-gray-50 text-gray-600 cursor-pointer">
                    <i class="fa-solid fa-user-shield w-5 text-center"></i>
                    <span>لوحة المسؤول</span>
                </button>
            </div>
        </aside>

        <!-- Dynamic Views -->
        <main class="flex-1 min-w-0">
            
            <!-- View 1: Booking Form -->
            <section id="booking-form" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8 fade-in">
                <h2 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">تقديم طلب حجز قاعة</h2>
                <form id="form-booking" class="space-y-6" onsubmit="handleFormSubmit(event)">
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">القاعة المطلوبة <span class="text-red-500">*</span></label>
                            <select id="hall" required class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                                <option value="" disabled selected>اختر القاعة...</option>
                                <option value="القاعة الكبيرة">القاعة الكبيرة</option>
                                <option value="القاعة الزجاجية">القاعة الزجاجية</option>
                                <option value="القاعة الداخلية">القاعة الداخلية</option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">تاريخ الحجز (الأحد - الخميس) <span class="text-red-500">*</span></label>
                            <input type="date" id="date" required onchange="validateDate(this)" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                        </div>

                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">وقت الحجز (ساعة واحدة) <span class="text-red-500">*</span></label>
                            <select id="time" required class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                                <option value="" disabled selected>اختر الوقت...</option>
                                <option value="08:00 - 09:00">08:00 صباحاً - 09:00 صباحاً</option>
                                <option value="09:00 - 10:00">09:00 صباحاً - 10:00 صباحاً</option>
                                <option value="10:00 - 11:00">10:00 صباحاً - 11:00 صباحاً</option>
                                <option value="11:00 - 12:00">11:00 صباحاً - 12:00 مساءً</option>
                                <option value="12:00 - 13:00">12:00 مساءً - 01:00 مساءً</option>
                                <option value="13:00 - 14:00">01:00 مساءً - 02:00 مساءً</option>
                                <option value="14:00 - 15:00">02:00 مساءً - 03:00 مساءً</option>
                                <option value="15:00 - 16:00">03:00 مساءً - 04:00 مساءً</option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">القسم مقدم الطلب <span class="text-red-500">*</span></label>
                            <input type="text" id="department" required placeholder="مثال: قسم الباطنية" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                        </div>
                    </div>

                    <hr class="border-gray-100">

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">عنوان المحاضرة / الاجتماع <span class="text-red-500">*</span></label>
                            <input type="text" id="title" required placeholder="موضوع الحجز" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                        </div>

                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">اسم المحاضر / المتحدث</label>
                            <input type="text" id="lecturer" placeholder="اختياري" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                        </div>

                        <div class="md:col-span-2">
                            <label class="block text-sm font-semibold text-gray-700 mb-2">اسم مقدم الطلب وبيانات التواصل <span class="text-red-500">*</span></label>
                            <input type="text" id="requester" required placeholder="الاسم ورقم التحويلة أو الجوال" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-medical-500 focus:border-medical-500 outline-none transition-all">
                        </div>
                    </div>

                    <div class="flex items-center gap-4 mt-8 bg-blue-50 p-4 rounded-lg border border-blue-100 text-blue-800 text-sm">
                        <i class="fa-solid fa-circle-info text-xl"></i>
                        <p>تنويه: تقديم الطلب لا يعني التأكيد. سيتم مراجعة الطلب من قبل مسؤول القاعات وإشعاركم بالاعتماد.</p>
                    </div>

                    <button type="submit" class="w-full bg-medical-600 hover:bg-medical-700 text-white font-bold py-3.5 px-4 rounded-lg shadow-md transition-all active:transform active:scale-95 flex justify-center items-center gap-2 text-lg">
                        <i class="fa-regular fa-paper-plane"></i> إرسال طلب الحجز
                    </button>
                </form>
            </section>

            <!-- View 2: Schedule View -->
            <section id="schedule-view" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8 hidden fade-in">
                <div class="flex justify-between items-center mb-6 border-b pb-4">
                    <h2 class="text-2xl font-bold text-gray-800">جدول الحجوزات المعتمدة</h2>
                    <div class="flex gap-2 text-sm">
                        <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full font-semibold">مؤكد</span>
                        <span class="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full font-semibold">قيد المراجعة</span>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-right border-collapse">
                        <thead>
                            <tr class="bg-gray-50 text-gray-600 border-y border-gray-200">
                                <th class="py-3 px-4 font-semibold">التاريخ والوقت</th>
                                <th class="py-3 px-4 font-semibold">القاعة</th>
                                <th class="py-3 px-4 font-semibold">العنوان</th>
                                <th class="py-3 px-4 font-semibold">القسم</th>
                                <th class="py-3 px-4 font-semibold text-center">الحالة</th>
                            </tr>
                        </thead>
                        <tbody id="schedule-tbody" class="divide-y divide-gray-100"></tbody>
                    </table>
                    <div id="schedule-empty" class="hidden flex-col items-center justify-center py-12 text-gray-400">
                        <i class="fa-regular fa-calendar-xmark text-5xl mb-4"></i>
                        <p class="text-lg">لا توجد حجوزات مسجلة حالياً</p>
                    </div>
                </div>
            </section>

            <!-- View 3: Admin View -->
            <section id="admin-view" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8 hidden fade-in">
                <div class="flex justify-between items-center mb-6 border-b pb-4">
                    <h2 class="text-2xl font-bold text-gray-800">لوحة تحكم مسؤول القاعات</h2>
                    <span class="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full"><i class="fa-solid fa-lock ml-1"></i> صلاحيات إدارية</span>
                </div>

                <h3 class="font-semibold text-lg mb-4 text-gray-700">الطلبات المعلقة (تحتاج إجراء)</h3>
                
                <div class="grid grid-cols-1 gap-4" id="admin-requests"></div>
                <div id="admin-empty" class="hidden flex-col items-center justify-center py-10 text-gray-400 bg-gray-50 rounded-lg border border-dashed border-gray-200 mt-4">
                    <i class="fa-solid fa-check-double text-4xl mb-3 text-green-300"></i>
                    <p>رائع! لا توجد طلبات معلقة بانتظار المراجعة.</p>
                </div>
            </section>

        </main>
    </div>

    <!-- Alerts Modal -->
    <div id="customModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 hidden opacity-0 transition-opacity duration-300">
        <div class="bg-white rounded-xl shadow-2xl p-6 sm:p-8 max-w-sm w-full mx-4 transform scale-95 transition-transform duration-300" id="modalContent">
            <div id="modalIcon" class="text-5xl text-center mb-4"></div>
            <h3 id="modalTitle" class="text-xl font-bold text-center text-gray-800 mb-2"></h3>
            <p id="modalMessage" class="text-center text-gray-600 mb-6 leading-relaxed"></p>
            <button onclick="closeModal()" class="w-full bg-gray-800 hover:bg-gray-900 text-white font-bold py-3 px-4 rounded-lg transition-colors">حسناً</button>
        </div>
    </div>

    <script>
        // المتغيرات تُحدث الآن عبر اتصال بالخادم (Python)
        let bookings = [];

        document.addEventListener('DOMContentLoaded', () => {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('date').setAttribute('min', today);
            loadBookings();
        });

        // جلب البيانات من سيرفر بايثون
        async function loadBookings() {
            try {
                const response = await fetch('/api/bookings');
                bookings = await response.json();
                renderSchedule();
                renderAdmin();
            } catch (error) {
                console.error("Error loading bookings:", error);
            }
        }

        function switchTab(tabId) {
            document.getElementById('booking-form').classList.add('hidden');
            document.getElementById('schedule-view').classList.add('hidden');
            document.getElementById('admin-view').classList.add('hidden');
            
            const btns = ['btn-booking-form', 'btn-schedule-view', 'btn-admin-view'];
            btns.forEach(btn => {
                const el = document.getElementById(btn);
                el.classList.remove('bg-medical-50', 'text-medical-700', 'font-semibold');
                el.classList.add('hover:bg-gray-50', 'text-gray-600');
            });

            document.getElementById(tabId).classList.remove('hidden');
            const activeBtn = document.getElementById(`btn-${tabId}`);
            activeBtn.classList.remove('hover:bg-gray-50', 'text-gray-600');
            activeBtn.classList.add('bg-medical-50', 'text-medical-700', 'font-semibold');
        }

        function validateDate(input) {
            const dateVal = new Date(input.value);
            const day = dateVal.getDay(); 
            if (day === 5 || day === 6) {
                showModal('تاريخ غير متاح', 'عذراً، لا يمكن الحجز في أيام عطلة نهاية الأسبوع (الجمعة والسبت). يرجى اختيار يوم عمل.', 'error');
                input.value = '';
            }
        }

        // إرسال طلب حجز جديد لسيرفر بايثون
        async function handleFormSubmit(e) {
            e.preventDefault();

            const hall = document.getElementById('hall').value;
            const date = document.getElementById('date').value;
            const time = document.getElementById('time').value;
            const department = document.getElementById('department').value;
            const title = document.getElementById('title').value;
            const lecturer = document.getElementById('lecturer').value;
            const requester = document.getElementById('requester').value;

            const newBooking = { hall, date, time, department, title, lecturer, requester };

            try {
                const response = await fetch('/api/bookings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newBooking)
                });

                if (!response.ok) {
                    const data = await response.json();
                    showModal('تعارض في الحجز', data.error, 'error');
                    return;
                }

                const createdBooking = await response.json();
                bookings.push(createdBooking); 

                e.target.reset();
                showModal('تم إرسال الطلب بنجاح', 'تم استلام طلب الحجز وهو الآن قيد المراجعة من قبل مسؤول القاعات.', 'success');
                
                renderSchedule();
                renderAdmin();
            } catch (error) {
                showModal('خطأ في الاتصال', 'تعذر الاتصال بالخادم، تأكد من تشغيل ملف البايثون', 'error');
            }
        }

        // تحديث حالة الطلب عبر سيرفر بايثون
        async function updateStatus(id, newStatus) {
            try {
                const response = await fetch(`/api/bookings/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });

                if (response.ok) {
                    const index = bookings.findIndex(b => b.id === id);
                    if (index !== -1) {
                        bookings[index].status = newStatus;
                        renderAdmin();
                        renderSchedule();
                        const msg = newStatus === 'approved' ? 'تم اعتماد الحجز بنجاح' : 'تم رفض الحجز';
                        showModal('تم التحديث', msg, 'success');
                    }
                }
            } catch (error) {
                showModal('خطأ', 'حدث خطأ أثناء تحديث حالة الطلب', 'error');
            }
        }

        function renderSchedule() {
            const tbody = document.getElementById('schedule-tbody');
            const emptyState = document.getElementById('schedule-empty');
            tbody.innerHTML = '';

            const visibleBookings = bookings.filter(b => b.status !== 'rejected')
                                          .sort((a, b) => new Date(a.date) - new Date(b.date));

            if (visibleBookings.length === 0) {
                emptyState.classList.remove('hidden');
                emptyState.classList.add('flex');
                tbody.parentElement.classList.add('hidden');
            } else {
                emptyState.classList.add('hidden');
                emptyState.classList.remove('flex');
                tbody.parentElement.classList.remove('hidden');

                visibleBookings.forEach(b => {
                    const statusBadge = b.status === 'approved' 
                        ? `<span class="px-2.5 py-1 text-xs bg-green-100 text-green-800 rounded-full"><i class="fa-solid fa-check mr-1"></i> مؤكد</span>`
                        : `<span class="px-2.5 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full"><i class="fa-regular fa-clock mr-1"></i> مراجعة</span>`;

                    const tr = document.createElement('tr');
                    tr.className = "hover:bg-gray-50 transition-colors";
                    tr.innerHTML = `
                        <td class="py-4 px-4 border-b border-gray-100">
                            <div class="font-semibold text-gray-800">${b.date}</div>
                            <div class="text-sm text-gray-500" dir="ltr">${b.time}</div>
                        </td>
                        <td class="py-4 px-4 border-b border-gray-100 font-medium text-medical-700">${b.hall}</td>
                        <td class="py-4 px-4 border-b border-gray-100 text-gray-800">${b.title}</td>
                        <td class="py-4 px-4 border-b border-gray-100 text-sm text-gray-600">${b.department}</td>
                        <td class="py-4 px-4 border-b border-gray-100 text-center">${statusBadge}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }

        function renderAdmin() {
            const container = document.getElementById('admin-requests');
            const emptyState = document.getElementById('admin-empty');
            container.innerHTML = '';

            const pendingRequests = bookings.filter(b => b.status === 'pending');

            if (pendingRequests.length === 0) {
                emptyState.classList.remove('hidden');
                emptyState.classList.add('flex');
            } else {
                emptyState.classList.add('hidden');
                emptyState.classList.remove('flex');

                pendingRequests.forEach(b => {
                    const card = document.createElement('div');
                    card.className = "bg-white p-5 rounded-lg border border-gray-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-medical-300 transition-colors";
                    
                    card.innerHTML = `
                        <div class="flex-1">
                            <div class="flex flex-wrap items-center gap-2 mb-2">
                                <span class="bg-medical-100 text-medical-800 text-xs px-2 py-1 rounded font-bold">${b.hall}</span>
                                <span class="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded font-mono" dir="ltr">${b.date} | ${b.time}</span>
                            </div>
                            <h4 class="font-bold text-gray-800 text-lg">${b.title}</h4>
                            <div class="text-sm text-gray-600 mt-1 flex flex-col sm:flex-row sm:gap-4">
                                <span><i class="fa-solid fa-sitemap text-gray-400 ml-1"></i>القسم: ${b.department}</span>
                                <span><i class="fa-solid fa-user text-gray-400 ml-1"></i>الطلب: ${b.requester}</span>
                            </div>
                        </div>
                        <div class="flex gap-2 w-full md:w-auto">
                            <button onclick="updateStatus(${b.id}, 'approved')" class="flex-1 md:flex-none bg-green-50 hover:bg-green-500 text-green-700 hover:text-white border border-green-200 hover:border-green-500 transition-colors px-4 py-2 rounded-lg font-semibold flex justify-center items-center gap-2">
                                <i class="fa-solid fa-check"></i> اعتماد
                            </button>
                            <button onclick="updateStatus(${b.id}, 'rejected')" class="flex-1 md:flex-none bg-red-50 hover:bg-red-500 text-red-700 hover:text-white border border-red-200 hover:border-red-500 transition-colors px-4 py-2 rounded-lg font-semibold flex justify-center items-center gap-2">
                                <i class="fa-solid fa-xmark"></i> رفض
                            </button>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        }

        function showModal(title, message, type = 'info') {
            const modal = document.getElementById('customModal');
            const content = document.getElementById('modalContent');
            const icon = document.getElementById('modalIcon');
            
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalMessage').textContent = message;

            if (type === 'success') {
                icon.innerHTML = '<i class="fa-regular fa-circle-check text-green-500"></i>';
            } else if (type === 'error') {
                icon.innerHTML = '<i class="fa-regular fa-circle-xmark text-red-500"></i>';
            } else {
                icon.innerHTML = '<i class="fa-solid fa-circle-info text-blue-500"></i>';
            }

            modal.classList.remove('hidden');
            setTimeout(() => {
                modal.classList.remove('opacity-0');
                content.classList.remove('scale-95');
                content.classList.add('scale-100');
            }, 10);
        }

        function closeModal() {
            const modal = document.getElementById('customModal');
            const content = document.getElementById('modalContent');
            modal.classList.add('opacity-0');
            content.classList.remove('scale-100');
            content.classList.add('scale-95');
            setTimeout(() => modal.classList.add('hidden'), 300);
        }
    </script>
</body>
</html>
"""

# --- منطق معالجة طلبات المتصفح ---
class BookingHandler(BaseHTTPRequestHandler):
    def _send_response(self, response_code, content, content_type='application/json'):
        self.send_response(response_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*') # تفعيل CORS لسهولة التطوير
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/':
            # إرسال صفحة واجهة المستخدم HTML
            self._send_response(200, HTML_CONTENT.encode('utf-8'), 'text/html; charset=utf-8')
        elif parsed_path.path == '/api/bookings':
            # إرسال قائمة الحجوزات
            self._send_response(200, json.dumps(bookings).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/bookings':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # التحقق من التعارض على مستوى البايثون (Backend)
            for b in bookings:
                if b['hall'] == data['hall'] and b['date'] == data['date'] and b['time'] == data['time'] and b['status'] in ['approved', 'pending']:
                    self._send_response(400, json.dumps({'error': f"عذراً، {data['hall']} محجوزة مسبقاً (أو قيد المراجعة) في هذا الوقت."}).encode('utf-8'))
                    return

            new_booking = {
                'id': int(time.time() * 1000), # توليد ID فريد
                'hall': data['hall'],
                'date': data['date'],
                'time': data['time'],
                'department': data['department'],
                'title': data['title'],
                'lecturer': data.get('lecturer', ''),
                'requester': data['requester'],
                'status': 'pending'
            }
            bookings.append(new_booking)
            self._send_response(201, json.dumps(new_booking).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/api/bookings/'):
            try:
                booking_id = int(parsed_path.path.split('/')[-1])
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                data = json.loads(put_data.decode('utf-8'))
                
                # تحديث حالة الطلب
                for b in bookings:
                    if b['id'] == booking_id:
                        b['status'] = data['status']
                        self._send_response(200, json.dumps(b).encode('utf-8'))
                        return
                self._send_response(404, json.dumps({'error': 'Not found'}).encode('utf-8'))
            except ValueError:
                self._send_response(400, json.dumps({'error': 'Invalid ID'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

# --- دالة تشغيل السيرفر ---
def run_server():
    # قراءة المنفذ من الخادم السحابي (أو استخدام 8000 محلياً)
    port = int(os.environ.get("PORT", 8000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, BookingHandler)
    print("========================================")
    print(f"تم تشغيل خادم بايثون بنجاح على المنفذ: {port}")
    print("========================================")
    print("لإيقاف الخادم اضغط CTRL+C")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("\nتم إيقاف الخادم.")

if __name__ == '__main__':
    run_server()