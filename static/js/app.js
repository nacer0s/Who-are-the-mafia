// لعبة المافيا - JavaScript الرئيسي

class MafiaGame {
    constructor() {
        this.socket = null;
        this.currentUser = null;
        this.currentRoom = null;
        this.gameState = null;
        this.init();
    }

    init() {
        this.initSocket();
        this.bindEvents();
        this.updateConnectionStatus();
        this.loadUserData();
    }

    // إعداد Socket.IO
    initSocket() {
        this.socket = io({
            transports: ['websocket', 'polling'],
            timeout: 5000,
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });

        // أحداث الاتصال
        this.socket.on('connect', () => {
            console.log('متصل بالخادم');
            this.updateConnectionStatus(true);
            this.loadUserData();
        });

        this.socket.on('disconnect', () => {
            console.log('انقطع الاتصال بالخادم');
            this.updateConnectionStatus(false);
        });

        this.socket.on('reconnect', () => {
            console.log('تم إعادة الاتصال');
            this.loadUserData();
        });

        // أحداث الغرف
        this.socket.on('room_joined', (data) => {
            this.currentRoom = data.room;
            this.showNotification('تم الانضمام للغرفة بنجاح', 'success');
            if (window.location.pathname.includes('game')) {
                this.updateRoomDisplay();
            }
        });

        this.socket.on('room_left', (data) => {
            this.currentRoom = null;
            this.showNotification('تم مغادرة الغرفة', 'info');
        });

        this.socket.on('player_joined', (data) => {
            this.showNotification(`انضم ${data.player.display_name} للغرفة`, 'info');
            this.updatePlayersList();
        });

        this.socket.on('player_left', (data) => {
            this.showNotification(`غادر ${data.player.display_name} الغرفة`, 'warning');
            this.updatePlayersList();
        });

        // أحداث اللعبة
        this.socket.on('game_started', (data) => {
            this.gameState = data.game_state;
            this.showNotification('بدأت اللعبة!', 'success');
            this.updateGameDisplay();
        });

        this.socket.on('game_phase_changed', (data) => {
            this.gameState.phase = data.phase;
            this.updatePhaseDisplay();
            this.showPhaseNotification(data.phase);
        });

        this.socket.on('role_assigned', (data) => {
            this.currentUser.role = data.role;
            this.showRoleNotification(data.role);
            this.updateRoleDisplay();
        });

        this.socket.on('player_died', (data) => {
            this.showNotification(`${data.player.display_name} قُتل!`, 'danger');
            this.updatePlayersList();
        });

        this.socket.on('game_ended', (data) => {
            this.showGameResult(data.result);
            this.gameState = null;
        });

        // أحداث الدردشة
        this.socket.on('new_message', (data) => {
            this.addMessage(data.message);
        });

        this.socket.on('message_hidden', (data) => {
            this.hideMessage(data.message_id, data.reason);
        });

        this.socket.on('voice_transcribed', (data) => {
            this.addTranscription(data);
        });

        // أحداث التصويت
        this.socket.on('vote_cast', (data) => {
            this.updateVoteDisplay(data);
        });

        this.socket.on('vote_result', (data) => {
            this.showVoteResult(data);
        });

        // أحداث أخرى
        this.socket.on('notification', (data) => {
            this.showNotification(data.message, data.type);
        });

        this.socket.on('error', (data) => {
            this.showNotification(data.message, 'danger');
        });
    }

    // ربط الأحداث
    bindEvents() {
        // نموذج تسجيل الدخول
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // نموذج التسجيل
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // إنشاء غرفة
        const createRoomBtn = document.getElementById('createRoomBtn');
        if (createRoomBtn) {
            createRoomBtn.addEventListener('click', () => this.showCreateRoomModal());
        }

        // الانضمام لغرفة
        const joinRoomBtn = document.getElementById('joinRoomBtn');
        if (joinRoomBtn) {
            joinRoomBtn.addEventListener('click', () => this.showJoinRoomModal());
        }

        // إرسال رسالة
        const messageForm = document.getElementById('messageForm');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => this.sendMessage(e));
        }

        // تسجيل صوتي
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());
        }

        // بدء اللعبة
        const startGameBtn = document.getElementById('startGameBtn');
        if (startGameBtn) {
            startGameBtn.addEventListener('click', () => this.startGame());
        }

        // تبديل الاستعداد
        const readyBtn = document.getElementById('readyBtn');
        if (readyBtn) {
            readyBtn.addEventListener('click', () => this.toggleReady());
        }
    }

    // تحديث حالة الاتصال
    updateConnectionStatus(connected = false) {
        const onlineStatus = document.getElementById('status-online');
        const offlineStatus = document.getElementById('status-offline');
        
        if (connected) {
            onlineStatus.style.display = 'block';
            offlineStatus.style.display = 'none';
        } else {
            onlineStatus.style.display = 'none';
            offlineStatus.style.display = 'block';
        }
    }

    // تحميل بيانات المستخدم
    async loadUserData() {
        try {
            const response = await fetch('/api/auth/me');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.currentUser = data.user;
                    this.socket.emit('authenticate', { user_id: this.currentUser.id });
                }
            }
        } catch (error) {
            console.log('المستخدم غير مسجل الدخول');
        }
    }

    // تسجيل الدخول
    async handleLogin(event) {
        event.preventDefault();
        this.showLoading('جاري تسجيل الدخول...');

        const formData = new FormData(event.target);
        const loginData = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(loginData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('تم تسجيل الدخول بنجاح', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);
            } else {
                this.showNotification(result.message, 'danger');
            }
        } catch (error) {
            this.showNotification('خطأ في الاتصال بالخادم', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    // التسجيل
    async handleRegister(event) {
        event.preventDefault();
        this.showLoading('جاري إنشاء الحساب...');

        const formData = new FormData(event.target);
        const registerData = {
            username: formData.get('username'),
            display_name: formData.get('display_name'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        // التحقق من تطابق كلمة المرور
        if (registerData.password !== formData.get('confirm_password')) {
            this.showNotification('كلمات المرور غير متطابقة', 'danger');
            this.hideLoading();
            return;
        }

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(registerData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('تم إنشاء الحساب بنجاح', 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1000);
            } else {
                this.showNotification(result.message, 'danger');
            }
        } catch (error) {
            this.showNotification('خطأ في الاتصال بالخادم', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    // إنشاء غرفة
    showCreateRoomModal() {
        const modal = new bootstrap.Modal(document.getElementById('createRoomModal'));
        modal.show();
    }

    async createRoom() {
        const formData = new FormData(document.getElementById('createRoomForm'));
        const roomData = {
            name: formData.get('name'),
            max_players: parseInt(formData.get('max_players')),
            min_players: parseInt(formData.get('min_players')),
            allow_voice_chat: formData.get('allow_voice_chat') === 'on',
            password: formData.get('password') || null
        };

        this.showLoading('جاري إنشاء الغرفة...');

        try {
            const response = await fetch('/api/room/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(roomData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('تم إنشاء الغرفة بنجاح', 'success');
                setTimeout(() => {
                    window.location.href = `/game/${result.room.room_code}`;
                }, 1000);
            } else {
                this.showNotification(result.message, 'danger');
            }
        } catch (error) {
            this.showNotification('خطأ في إنشاء الغرفة', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    // الانضمام لغرفة
    showJoinRoomModal() {
        const modal = new bootstrap.Modal(document.getElementById('joinRoomModal'));
        modal.show();
    }

    async joinRoom() {
        const formData = new FormData(document.getElementById('joinRoomForm'));
        const joinData = {
            room_code: formData.get('room_code'),
            password: formData.get('password') || null
        };

        this.showLoading('جاري الانضمام للغرفة...');

        try {
            const response = await fetch('/api/room/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(joinData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('تم الانضمام للغرفة بنجاح', 'success');
                setTimeout(() => {
                    window.location.href = `/game/${joinData.room_code}`;
                }, 1000);
            } else {
                this.showNotification(result.message, 'danger');
            }
        } catch (error) {
            this.showNotification('خطأ في الانضمام للغرفة', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    // إرسال رسالة
    sendMessage(event) {
        event.preventDefault();
        
        const messageInput = document.getElementById('messageInput');
        const content = messageInput.value.trim();
        
        if (!content) return;

        this.socket.emit('send_message', {
            content: content,
            message_type: 'text'
        });

        messageInput.value = '';
    }

    // إضافة رسالة للدردشة
    addMessage(message) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.message_type}`;
        messageElement.dataset.messageId = message.id;

        if (message.is_flagged) {
            messageElement.classList.add('suspicious');
        }

        const time = new Date(message.sent_at).toLocaleTimeString('ar-SA', {
            hour: '2-digit',
            minute: '2-digit'
        });

        let content = '';
        if (message.user_id) {
            content = `
                <div class="message-header">${message.user.display_name}</div>
                <div class="message-time">${time}</div>
                <div class="message-content">${this.escapeHtml(message.content)}</div>
            `;
        } else {
            content = `
                <div class="message-content">${this.escapeHtml(message.content)}</div>
                <div class="message-time">${time}</div>
            `;
        }

        messageElement.innerHTML = content;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // إضافة مؤشر الشك إذا كان موجوداً
        if (message.suspicion_score > 0) {
            this.addSuspicionBar(messageElement, message.suspicion_score);
        }
    }

    // إخفاء رسالة
    hideMessage(messageId, reason) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            messageElement.classList.add('suspicious');
            const contentElement = messageElement.querySelector('.message-content');
            contentElement.innerHTML = `<em>تم إخفاء هذه الرسالة: ${reason}</em>`;
        }
    }

    // إضافة شريط الشك
    addSuspicionBar(messageElement, score) {
        const suspicionBar = document.createElement('div');
        suspicionBar.className = 'suspicion-bar';
        suspicionBar.innerHTML = `<div class="suspicion-fill" style="width: ${score * 100}%"></div>`;
        messageElement.appendChild(suspicionBar);
    }

    // بدء اللعبة
    async startGame() {
        this.showLoading('جاري بدء اللعبة...');

        try {
            const response = await fetch('/api/game/start', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (!result.success) {
                this.showNotification(result.message, 'danger');
            }
        } catch (error) {
            this.showNotification('خطأ في بدء اللعبة', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    // تبديل حالة الاستعداد
    toggleReady() {
        this.socket.emit('toggle_ready');
    }

    // تحديث عرض اللعبة
    updateGameDisplay() {
        if (!this.gameState) return;

        this.updatePhaseDisplay();
        this.updatePlayersList();
        this.updateRoleDisplay();
    }

    // تحديث عرض المرحلة
    updatePhaseDisplay() {
        const phaseElement = document.getElementById('gamePhase');
        if (!phaseElement || !this.gameState) return;

        const phase = this.gameState.phase;
        phaseElement.className = `game-phase phase-${phase.phase}`;
        
        let phaseText = '';
        switch (phase.phase) {
            case 'night':
                phaseText = '🌙 الليل - وقت عمل الأدوار الخاصة';
                break;
            case 'day':
                phaseText = '☀️ النهار - وقت النقاش';
                break;
            case 'vote':
                phaseText = '🗳️ التصويت - اختر من تريد إعدامه';
                break;
        }

        phaseElement.innerHTML = `
            <h3>${phaseText}</h3>
            <div class="phase-timer">الوقت المتبقي: <span id="phaseTimer">${phase.time_left}</span> ثانية</div>
        `;

        this.startPhaseTimer(phase.time_left);
    }

    // مؤقت المرحلة
    startPhaseTimer(timeLeft) {
        const timerElement = document.getElementById('phaseTimer');
        if (!timerElement) return;

        const timer = setInterval(() => {
            timeLeft--;
            timerElement.textContent = timeLeft;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
            }
        }, 1000);
    }

    // تحديث قائمة اللاعبين
    updatePlayersList() {
        const playersContainer = document.getElementById('playersList');
        if (!playersContainer || !this.gameState) return;

        playersContainer.innerHTML = '';

        this.gameState.players.forEach(player => {
            const playerElement = document.createElement('div');
            playerElement.className = 'player-item';
            playerElement.dataset.playerId = player.id;

            const roleClass = player.is_alive ? 'player-alive' : 'player-dead';
            const statusText = player.is_alive ? 'حي' : 'ميت';

            playerElement.innerHTML = `
                <div class="player-avatar">${player.display_name[0]}</div>
                <div class="player-info">
                    <div class="player-name">${player.display_name}</div>
                    <div class="player-status">
                        <span class="player-role ${roleClass}">${statusText}</span>
                        ${player.is_ready ? '<i class="fas fa-check text-success"></i>' : ''}
                    </div>
                </div>
            `;

            // إضافة مؤشر النشاط
            if (player.is_online) {
                const indicator = document.createElement('div');
                indicator.className = 'activity-indicator';
                playerElement.appendChild(indicator);
            }

            playersContainer.appendChild(playerElement);
        });
    }

    // تحديث عرض الدور
    updateRoleDisplay() {
        const roleElement = document.getElementById('playerRole');
        if (!roleElement || !this.currentUser.role) return;

        const roleNames = {
            'civilian': 'مواطن',
            'mafia': 'مافيا',
            'doctor': 'طبيب',
            'detective': 'محقق',
            'vigilante': 'عدالة شعبية',
            'mayor': 'عمدة',
            'jester': 'مهرج'
        };

        const roleName = roleNames[this.currentUser.role] || this.currentUser.role;
        roleElement.innerHTML = `
            <div class="role-card role-${this.currentUser.role}">
                <h5>دورك: ${roleName}</h5>
                <div class="role-description">${this.getRoleDescription(this.currentUser.role)}</div>
            </div>
        `;
    }

    // وصف الأدوار
    getRoleDescription(role) {
        const descriptions = {
            'civilian': 'أنت مواطن عادي. هدفك القضاء على المافيا بالتصويت نهاراً.',
            'mafia': 'أنت من المافيا. اقتل المواطنين ليلاً واخفِ هويتك نهاراً.',
            'doctor': 'أنت الطبيب. احمِ لاعباً واحداً كل ليلة من القتل.',
            'detective': 'أنت المحقق. تحقق من هوية لاعب واحد كل ليلة.',
            'vigilante': 'أنت العدالة الشعبية. يمكنك قتل لاعب واحد كل ليلة.',
            'mayor': 'أنت العمدة. صوتك يحسب بصوتين في التصويت.',
            'jester': 'أنت المهرج. تفوز إذا تم إعدامك بالتصويت نهاراً.'
        };
        return descriptions[role] || 'دور غير معروف';
    }

    // إظهار نتيجة اللعبة
    showGameResult(result) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-${result.winner === 'civilians' ? 'success' : 'danger'}">
                        <h5 class="modal-title text-white">
                            ${result.winner === 'civilians' ? '🏆 فاز المواطنون!' : '🏆 فازت المافيا!'}
                        </h5>
                    </div>
                    <div class="modal-body">
                        <div class="game-summary">
                            <h6>ملخص اللعبة:</h6>
                            <ul>
                                <li>المدة: ${result.duration} دقيقة</li>
                                <li>عدد الجولات: ${result.rounds}</li>
                                <li>اللاعبون الناجون: ${result.survivors.length}</li>
                            </ul>
                        </div>
                        <div class="players-result mt-3">
                            <h6>نتائج اللاعبين:</h6>
                            <div class="row">
                                ${result.players.map(player => `
                                    <div class="col-md-6 mb-2">
                                        <div class="player-result">
                                            <strong>${player.display_name}</strong>
                                            <span class="role-badge role-${player.role}">${player.role}</span>
                                            ${player.is_winner ? '<i class="fas fa-crown text-warning"></i>' : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="location.reload()">
                            لعبة جديدة
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="location.href='/rooms'">
                            العودة للغرف
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    // إظهار إشعار الدور
    showRoleNotification(role) {
        const roleNames = {
            'civilian': 'مواطن',
            'mafia': 'مافيا',
            'doctor': 'طبيب',
            'detective': 'محقق',
            'vigilante': 'عدالة شعبية',
            'mayor': 'عمدة',
            'jester': 'مهرج'
        };

        const roleName = roleNames[role] || role;
        this.showNotification(`تم تعيين دورك: ${roleName}`, 'info', 5000);
    }

    // إظهار إشعار المرحلة
    showPhaseNotification(phase) {
        const phaseNames = {
            'night': 'بدأ الليل 🌙',
            'day': 'بدأ النهار ☀️',
            'vote': 'بدأ التصويت 🗳️'
        };

        const phaseName = phaseNames[phase.phase] || phase.phase;
        this.showNotification(phaseName, 'info', 3000);
    }

    // إظهار الإشعارات
    showNotification(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // إنشاء حاوي الإشعارات إذا لم تكن موجودة
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // إزالة الإشعار بعد إخفائه
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // إظهار شاشة التحميل
    showLoading(text = 'جاري التحميل...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        
        if (overlay && loadingText) {
            loadingText.textContent = text;
            overlay.style.display = 'flex';
        }
    }

    // إخفاء شاشة التحميل
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // تنظيف HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // معاينة الملف الصوتي
    previewVoiceMessage(file) {
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = URL.createObjectURL(file);
        return audio;
    }

    // تسجيل صوتي (سيتم تطويره لاحقاً)
    toggleVoiceRecording() {
        this.showNotification('ميزة التسجيل الصوتي قيد التطوير', 'info');
    }
}

// تشغيل التطبيق عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    window.mafiaGame = new MafiaGame();
});

// دوال مساعدة عامة
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA') + ' ' + date.toLocaleTimeString('ar-SA', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.mafiaGame.showNotification('تم نسخ النص', 'success', 2000);
    }).catch(() => {
        window.mafiaGame.showNotification('فشل في نسخ النص', 'danger', 2000);
    });
}