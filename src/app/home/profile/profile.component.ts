import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { AuthService } from '../../services/auth.service';

interface UserProfile {
    username: string;
    email: string;
    avatar: string;
    joinDate: Date;
}

interface UserStats {
    totalComments: number;
    favorites: number;
    followers: number;
    totalPlaytime: number;
}

interface Comment {
    id: number;
    gameTitle: string;
    gameCover: string;
    text: string;
    date: Date;
    likes: number;
}



interface PasswordData {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
}

@Component({
    selector: 'app-profile',
    standalone: true,
    imports: [CommonModule, HeaderComponent, FooterComponent, FormsModule],
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
        username: '',
        email: '',
        avatar: '',
        joinDate: new Date()
    };

    constructor(
        private authService: AuthService,
        private router: Router
    ) { }

    ngOnInit(): void {
        // Load current user data from AuthService
        this.authService.getCurrentUser().subscribe(user => {
            if (user) {
                this.userProfile.username = user.username;
                this.userProfile.email = user.email;
                this.userProfile.joinDate = new Date(user.created_at);
            }
        });
    }

    userStats: UserStats = {
        totalComments: 42,
        favorites: 28,
        followers: 156,
        totalPlaytime: 1250
    };

    userComments: Comment[] = [
        {
            id: 1,
            gameTitle: 'The Witcher 3: Wild Hunt',
            gameCover: 'https://images.igdb.com/igdb/image/upload/t_cover_big/co5ume.webp',
            text: 'เกม RPG ที่ยอดเยี่ยมที่สุดเกมหนึ่ง เนื้อเรื่องลึกซึ้ง ตัวละครน่าจดจำ โลกกว้างใหญ่และสวยงาม ใช้เวลาเล่นไปกว่า 200 ชั่วโมงแล้วยังไม่เบื่อเลย แนะนำเลยครับ!',
            date: new Date('2024-11-20'),
            likes: 24
        },
        {
            id: 2,
            gameTitle: 'Elden Ring',
            gameCover: 'https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.webp',
            text: 'เกมที่ท้าทายและน่าติดตามมาก ระบบการต่อสู้ลื่นไหล โลกแบบ Open World ที่สวยงาม แต่ความยากอาจไม่เหมาะกับทุกคน ต้องอดทนและเรียนรู้ pattern ของ boss',
            date: new Date('2024-10-15'),
            likes: 18
        },
        {
            id: 3,
            gameTitle: 'Red Dead Redemption 2',
            gameCover: 'https://images.igdb.com/igdb/image/upload/t_cover_big/co1q1f.webp',
            text: 'ผลงานชิ้นเอกของ Rockstar เนื้อเรื่องสุดประทับใจ กราฟิกสวยสุดๆ รายละเอียดในเกมเยอะมาก ทุกอย่างรู้สึกมีชีวิตจริงๆ ต้องลองเล่นให้จบเลย',
            date: new Date('2024-09-28'),
            likes: 31
        },
        {
            id: 4,
            gameTitle: 'Cyberpunk 2077',
            gameCover: 'https://images.igdb.com/igdb/image/upload/t_cover_big/co5vg0.webp',
            text: 'หลังจากอัพเดทหลายรอบ ตอนนี้เกมดีขึ้นมากเลย เนื้อเรื่องดี โลกสวยงาม ระบบ combat สนุก แนะนำให้ลองเล่นดูครับ',
            date: new Date('2024-08-12'),
            likes: 15
        }
    ];


    passwordData: PasswordData = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    };

    setActiveTab(tabId: string): void {
        this.activeTab = tabId;
    }

    logout(): void {
        this.authService.logout();
        this.router.navigate(['/']);
    }
}
