import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { FooterComponent } from '../../shared/footer.component';
import { DialogModule } from 'primeng/dialog';
import { AuthService } from '../../services/auth.service';
import { ProfileService, UserProfile, UserStats, UserComment } from '../../services/profile.service';
import { CommentService } from '../../services/comment.service';

interface PasswordData {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
}

@Component({
    selector: 'app-profile',
    standalone: true,
    imports: [CommonModule, FooterComponent, FormsModule, DialogModule, RouterModule],
    templateUrl: './profile.component.html',
    styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {
    activeTab: string = 'comments';

    tabs = [
        { id: 'comments', label: 'คอมเมนต์ของฉัน', icon: 'pi pi-comment' },
        { id: 'settings', label: 'ตั้งค่า', icon: 'pi pi-cog' }
    ];

    userProfile: UserProfile = {
        id: 0,
        username: '',
        email: '',
        user_role: '',
        avatar_url: null,
        created_at: ''
    };

    userStats: UserStats = {
        total_comments: 0,
        favorites: 0
    };

    userComments: UserComment[] = [];

    // Pagination
    currentPage = 1;
    itemsPerPage = 5;

    get paginatedComments(): UserComment[] {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        return this.userComments.slice(startIndex, startIndex + this.itemsPerPage);
    }

    get totalPages(): number {
        return Math.ceil(this.userComments.length / this.itemsPerPage) || 1;
    }

    nextPage(): void {
        if (this.currentPage < this.totalPages) this.currentPage++;
    }

    prevPage(): void {
        if (this.currentPage > 1) this.currentPage--;
    }

    passwordData: PasswordData = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    };

    // Loading states
    isLoadingProfile = false;
    isLoadingComments = false;
    isLoadingStats = false;
    isSavingProfile = false;
    isChangingPassword = false;

    // Dialog states
    showEditDialog = false;
    showDeleteDialog = false;
    showAvatarDialog = false;
    showDeleteAvatarConfirm = false;
    showLogoutDialog = false;
    showLogoutSuccessDialog = false;
    showEditSuccessDialog = false;
    editingComment: UserComment | null = null;
    editingContent = '';
    deletingCommentId: number | null = null;

    // Success/Error dialog
    showMessageDialog = false;
    messageDialogTitle = '';
    messageDialogContent = '';
    messageDialogType: 'success' | 'error' = 'success';

    // Avatar upload
    selectedFile: File | null = null;
    avatarPreview: string | null = null;

    constructor(
        private authService: AuthService,
        private profileService: ProfileService,
        private commentService: CommentService,
        private router: Router
    ) { }

    ngOnInit(): void {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.router.navigate(['/login']);
            return;
        }

        this.loadProfile(user.id);
        this.loadStats(user.id);
        this.loadComments(user.id);
    }

    loadProfile(userId: number) {
        this.isLoadingProfile = true;
        this.profileService.getProfile(userId).subscribe({
            next: (profile) => {
                this.userProfile = profile;
                this.isLoadingProfile = false;
            },
            error: (err) => {
                console.error('Error loading profile:', err);
                this.isLoadingProfile = false;
            }
        });
    }

    loadStats(userId: number) {
        this.isLoadingStats = true;
        this.profileService.getUserStats(userId).subscribe({
            next: (stats) => {
                this.userStats = stats;
                this.isLoadingStats = false;
            },
            error: (err) => {
                console.error('Error loading stats:', err);
                this.isLoadingStats = false;
            }
        });
    }

    loadComments(userId: number) {
        this.isLoadingComments = true;
        this.profileService.getUserComments(userId).subscribe({
            next: (comments) => {
                this.userComments = comments;
                if (this.currentPage > this.totalPages) {
                    this.currentPage = this.totalPages;
                }
                this.isLoadingComments = false;
            },
            error: (err) => {
                console.error('Error loading comments:', err);
                this.isLoadingComments = false;
            }
        });
    }

    onFileSelected(event: any) {
        const file = event.target.files[0];
        if (file) {
            this.selectedFile = file;

            // Create preview
            const reader = new FileReader();
            reader.onload = (e: any) => {
                this.avatarPreview = e.target.result;
                this.uploadAvatar(e.target.result);
            };
            reader.readAsDataURL(file);
        }
    }

    uploadAvatar(base64: string) {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        this.profileService.updateAvatar(user.id, base64).subscribe({
            next: () => {
                this.userProfile.avatar_url = base64;
                this.showMessage('success', 'สำเร็จ', 'อัพโหลดรูปโปรไฟล์สำเร็จ');
                // Notify other components about profile update
                window.dispatchEvent(new Event('profileUpdated'));
            },
            error: (err) => {
                console.error('Error uploading avatar:', err);
                this.showMessage('error', 'เกิดข้อผิดพลาด', 'เกิดข้อผิดพลาดในการอัพโหลดรูป');
            }
        });
    }

    startEditComment(comment: UserComment) {
        this.editingComment = comment;
        this.editingContent = comment.content;
        this.showEditDialog = true;
    }

    saveEditComment() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.editingComment) return;

        if (!this.editingContent.trim()) {
            this.showMessage('error', 'กรุณากรอกข้อมูล', 'กรุณากรอกความคิดเห็น');
            return;
        }

        this.commentService.editComment(this.editingComment.id, user.id, this.editingContent).subscribe({
            next: () => {
                this.showEditDialog = false;
                this.editingComment = null;
                this.editingContent = '';
                this.loadComments(user.id);
                this.showEditSuccessDialog = true;
            },
            error: (err) => {
                console.error('Error editing comment:', err);
                this.showMessage('error', 'เกิดข้อผิดพลาด', 'เกิดข้อผิดพลาดในการแก้ไขความคิดเห็น');
            }
        });
    }

    cancelEdit() {
        this.showEditDialog = false;
        this.editingComment = null;
        this.editingContent = '';
    }

    startDeleteComment(commentId: number) {
        this.deletingCommentId = commentId;
        this.showDeleteDialog = true;
    }

    confirmDelete() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.deletingCommentId) return;

        this.commentService.deleteComment(this.deletingCommentId, user.id).subscribe({
            next: () => {
                this.showDeleteDialog = false;
                this.deletingCommentId = null;
                this.loadComments(user.id);
                this.loadStats(user.id); // Refresh stats
            },
            error: (err) => {
                console.error('Error deleting comment:', err);
                this.showMessage('error', 'เกิดข้อผิดพลาด', 'เกิดข้อผิดพลาดในการลบความคิดเห็น');
                this.showDeleteDialog = false;
            }
        });
    }

    cancelDelete() {
        this.showDeleteDialog = false;
        this.deletingCommentId = null;
    }

    saveAllSettings() {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        // Check if ANY password field is filled
        const hasPasswordData = this.passwordData.currentPassword || this.passwordData.newPassword || this.passwordData.confirmPassword;

        // If any password field is filled, validate all are filled
        if (hasPasswordData) {
            if (!this.passwordData.currentPassword || !this.passwordData.newPassword || !this.passwordData.confirmPassword) {
                this.showErrorDialog('ข้อมูลรหัสผ่านไม่ครบถ้วน', 'หากต้องการเปลี่ยนรหัสผ่าน กรุณากรอกข้อมูลรหัสผ่านให้ครบถ้วน');
                return;
            }

            if (this.passwordData.currentPassword === this.passwordData.newPassword) {
                this.showErrorDialog('รหัสผ่านซ้ำกัน', 'รหัสผ่านใหม่ต้องไม่เหมือนกับรหัสผ่านปัจจุบัน');
                return;
            }

            if (this.passwordData.newPassword !== this.passwordData.confirmPassword) {
                this.showErrorDialog('รหัสผ่านไม่ตรงกัน', 'รหัสผ่านใหม่และยืนยันรหัสผ่านไม่ตรงกัน');
                return;
            }

            if (this.passwordData.newPassword.length < 6) {
                this.showErrorDialog('รหัสผ่านสั้นเกินไป', 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร');
                return;
            }
        }

        this.isSavingProfile = true;

        this.profileService.updateProfile(user.id, this.userProfile.username, this.userProfile.email).subscribe({
            next: () => {
                this.isSavingProfile = false;

                // Update local storage
                user.username = this.userProfile.username;
                user.email = this.userProfile.email;
                localStorage.setItem('currentUser', JSON.stringify(user));

                // If password fields are filled, change password
                if (hasPasswordData) {
                    this.changePassword();
                } else {
                    this.showSuccessDialog('บันทึกข้อมูลสำเร็จ', 'ข้อมูลโปรไฟล์ของคุณได้รับการอัปเดตแล้ว');
                }
            },
            error: (err) => {
                console.error('Error saving profile:', err);
                this.isSavingProfile = false;
                if (err.status === 400) {
                    this.showErrorDialog('ไม่สามารถบันทึกข้อมูลได้', err.error.detail || 'ข้อมูลไม่ถูกต้อง');
                } else {
                    this.showErrorDialog('เกิดข้อผิดพลาด', 'ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่อีกครั้ง');
                }
            }
        });
    }

    changePassword() {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        if (!this.passwordData.currentPassword || !this.passwordData.newPassword || !this.passwordData.confirmPassword) {
            this.showErrorDialog('ข้อมูลไม่ครบถ้วน', 'กรุณากรอกข้อมูลรหัสผ่านให้ครบถ้วน');
            return;
        }

        if (this.passwordData.newPassword !== this.passwordData.confirmPassword) {
            this.showErrorDialog('รหัสผ่านไม่ตรงกัน', 'รหัสผ่านใหม่และยืนยันรหัสผ่านไม่ตรงกัน');
            return;
        }

        if (this.passwordData.newPassword.length < 6) {
            this.showErrorDialog('รหัสผ่านสั้นเกินไป', 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร');
            return;
        }

        this.isChangingPassword = true;

        this.profileService.changePassword(user.id, this.passwordData.currentPassword, this.passwordData.newPassword).subscribe({
            next: () => {
                this.passwordData = {
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: ''
                };
                this.isChangingPassword = false;
                this.showSuccessDialog('บันทึกข้อมูลสำเร็จ', 'ข้อมูลโปรไฟล์และรหัสผ่านของคุณได้รับการอัปเดตแล้ว');
            },
            error: (err) => {
                console.error('Error changing password:', err);
                this.isChangingPassword = false;
                if (err.status === 400) {
                    this.showErrorDialog('รหัสผ่านไม่ถูกต้อง', 'รหัสผ่านปัจจุบันที่คุณกรอกไม่ถูกต้อง');
                } else {
                    this.showErrorDialog('เกิดข้อผิดพลาด', 'ไม่สามารถเปลี่ยนรหัสผ่านได้ กรุณาลองใหม่อีกครั้ง');
                }
            }
        });
    }

    setActiveTab(tabId: string): void {
        this.activeTab = tabId;
    }

    logout(): void {
        this.showLogoutDialog = true;
    }

    confirmLogout(): void {
        this.showLogoutDialog = false;
        this.authService.logout();
        this.showLogoutSuccessDialog = true;
    }

    handleLogoutSuccess(): void {
        this.showLogoutSuccessDialog = false;
        this.router.navigate(['/']);
    }

    formatDate(dateString: string): string {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('th-TH');
    }

    getAvatarUrl(): string {
        return this.userProfile.avatar_url || '';
    }

    showSuccessDialog(title: string, message: string) {
        this.messageDialogTitle = title;
        this.messageDialogContent = message;
        this.messageDialogType = 'success';
        this.showMessageDialog = true;
    }

    showErrorDialog(title: string, message: string) {
        this.messageDialogTitle = title;
        this.messageDialogContent = message;
        this.messageDialogType = 'error';
        this.showMessageDialog = true;
    }

    // Helper method to show message dialog
    showMessage(type: 'success' | 'error', title: string, content: string) {
        this.messageDialogType = type;
        this.messageDialogTitle = title;
        this.messageDialogContent = content;
        this.showMessageDialog = true;
    }

    // Check if user has avatar
    hasAvatar(): boolean {
        return this.userProfile.avatar_url !== null && this.userProfile.avatar_url !== '';
    }

    // Trigger file upload
    triggerFileUpload() {
        this.showAvatarDialog = false;
        // Use setTimeout to ensure dialog is closed before triggering file input
        setTimeout(() => {
            const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
            if (fileInput) {
                fileInput.click();
            }
        }, 100);
    }

    // Show delete avatar confirmation dialog
    showDeleteAvatarDialog() {
        this.showAvatarDialog = false;
        this.showDeleteAvatarConfirm = true;
    }

    // Cancel delete avatar
    cancelDeleteAvatar() {
        this.showDeleteAvatarConfirm = false;
    }

    // Confirm delete avatar
    confirmDeleteAvatar() {
        this.showDeleteAvatarConfirm = false;
        this.deleteAvatar();
    }

    // Delete avatar
    deleteAvatar() {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        this.profileService.deleteAvatar(user.id).subscribe({
            next: () => {
                this.userProfile.avatar_url = null;
                this.avatarPreview = null;
                this.showMessage('success', 'สำเร็จ', 'ลบรูปโปรไฟล์สำเร็จ');
                // Notify other components about profile update
                window.dispatchEvent(new Event('profileUpdated'));
            },
            error: (err) => {
                console.error('Error deleting avatar:', err);
                this.showMessage('error', 'เกิดข้อผิดพลาด', 'เกิดข้อผิดพลาดในการลบรูป');
            }
        });
    }
}
