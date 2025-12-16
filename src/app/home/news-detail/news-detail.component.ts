import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';

interface NewsItem {
    id: number;
    title: string;
    category?: string;
    date?: string;
    description?: string;
    image: string;
    author?: string;
    readTime?: string;
    content?: string;
    tags?: string[];
}

@Component({
    selector: 'app-news-detail',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent],
    templateUrl: './news-detail.component.html',
    styleUrls: ['./news-detail.component.css']
})
export class NewsDetailComponent implements OnInit {
    newsId: number = 0;
    newsItem: NewsItem | null = null;
    relatedNews: NewsItem[] = [];

    // Mock data - ในอนาคตจะดึงจาก API
    private allNews: NewsItem[] = [
        {
            id: 1,
            title: 'Path of Exile 2 - Update 2.0.1',
            category: 'อัพเดท',
            date: '15 ธันวาคม 2567',
            author: 'Grinding Gear Games',
            readTime: '5 นาที',
            description: 'บททดสอบแห่งเช็คเคมา ผู้เล่นไม่พอใจกับการเผชิญกับบททดสอบแห่งเช็คเคมาโดยเฉพาะในการต่อสู้ระยะใกล้',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/2694490/header.jpg',
            tags: ['Path of Exile', 'Update', 'Patch Notes'],
            content: `
        <h2>การปรับปรุงบททดสอบแห่งเช็คเคมา</h2>
        <p>ผู้เล่นไม่พอใจกับการเผชิญกับบททดสอบแห่งเช็คเคมาโดยเฉพาะในการต่อสู้ระยะใกล้ เราจึงปรับวิธีคำนวณความเสียหายที่เกิดขึ้นกับเกียรติเมื่ออยู่ในระยะใกล้ และทำการแก้ไขบัคที่สำคัญที่ทำให้ผู้เล่นได้รับความเสียหายต่อเกียรติมากเกินไปจากความเสียหายต่อเนื่อง</p>
        
        <h3>การเปลี่ยนแปลงหลัก</h3>
        <ul>
          <li>ปรับสมดุลความเสียหายในการต่อสู้ระยะใกล้</li>
          <li>แก้ไขบัคที่ทำให้ได้รับความเสียหายมากเกินไป</li>
          <li>ปรับปรุงระบบเกียรติให้สมดุลมากขึ้น</li>
          <li>เพิ่มความยุติธรรมในการต่อสู้</li>
        </ul>

        <h3>รายละเอียดการอัพเดท</h3>
        <p>การอัพเดทครั้งนี้มุ่งเน้นไปที่การปรับปรุงประสบการณ์การเล่นโดยรวม โดยเฉพาะในส่วนของการต่อสู้ที่ผู้เล่นหลายคนรู้สึกว่ายากเกินไป ทีมพัฒนาได้รับฟังความคิดเห็นจากชุมชนและนำมาปรับปรุงให้เกมมีความสมดุลมากขึ้น</p>

        <p>นอกจากนี้ยังมีการแก้ไขบัคอื่นๆ อีกมากมายที่ส่งผลต่อประสบการณ์การเล่น รวมถึงการปรับปรุงประสิทธิภาพของเกมในบางพื้นที่</p>

        <h3>สิ่งที่จะมาในอนาคต</h3>
        <p>ทีมพัฒนายังคงทำงานอย่างหนักเพื่อปรับปรุงเกมต่อไป โดยจะมีการอัพเดทเพิ่มเติมในอนาคตอันใกล้ที่จะนำเสนอเนื้อหาใหม่และการปรับสมดุลเพิ่มเติม</p>
      `
        },
        {
            id: 2,
            title: 'Call of Duty เปิดตัวกิจกรรม Double XP ใหม่ในเดือนกุมภาพันธ์ 2025',
            category: 'ข่าวสาร',
            date: '14 ธันวาคม 2567',
            author: 'Activision',
            readTime: '3 นาที',
            description: 'ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg',
            tags: ['Call of Duty', 'Event', 'Double XP'],
            content: `
        <h2>กิจกรรม Double XP พิเศษ</h2>
        <p>Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone ผู้เล่นมีเวลาจนถึงกลางเดือนกุมภาพันธ์ 2025 เพื่อใช้ประโยชน์จากโปรโมชัน Call of Duty ที่เพิ่งเริ่มต้น</p>

        <h3>รายละเอียดกิจกรรม</h3>
        <ul>
          <li>ระยะเวลา: ตั้งแต่วันนี้ - กลางเดือนกุมภาพันธ์ 2025</li>
          <li>โหมดที่ร่วมรายการ: Black Ops 6 และ Warzone</li>
          <li>รางวัล: Double XP สำหรับทุกโหมด</li>
          <li>เงื่อนไข: ไม่มีเงื่อนไขพิเศษ เล่นได้เลย</li>
        </ul>

        <h3>วิธีการเข้าร่วม</h3>
        <p>ผู้เล่นสามารถเข้าร่วมกิจกรรมได้ทันทีโดยไม่ต้องลงทะเบียนเพิ่มเติม เพียงแค่เข้าเล่นเกมตามปกติ ระบบจะคำนวณ XP ที่ได้รับเป็น 2 เท่าโดยอัตโนมัติ</p>
      `
        },
        {
            id: 3,
            title: 'GTA 6 Release Date Still Set for Fall 2025',
            category: 'ข่าวสาร',
            date: '13 ธันวาคม 2567',
            author: 'Rockstar Games',
            readTime: '4 นาที',
            description: 'GTA 6 จะออกวางจำหน่ายในฤดูใบไม้ร่วงปี 2025',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg',
            tags: ['GTA 6', 'Release Date', 'Rockstar'],
            content: `
        <h2>ยืนยันวันวางจำหน่าย GTA 6</h2>
        <p>ตามรายงานผลประกอบการทางการเงินของ Take-Two ที่เกิดขึ้นเมื่อวันนี้ ณ เวลาที่บันทึกข้อมูลนี้ บริษัทแม่มั่นใจว่า GTA 6 จะออกวางจำหน่ายในฤดูใบไม้ร่วงปี 2025 นั่นหมายความว่าข่าวลือเรื่องการเลื่อนกำหนดวางจำหน่ายเป็นเพียงข่าวลือเท่านั้น</p>

        <h3>สิ่งที่คาดหวังได้</h3>
        <ul>
          <li>โลกเปิดที่ใหญ่ที่สุดในประวัติศาสตร์ GTA</li>
          <li>กราฟิกที่สมจริงด้วยเทคโนโลยีล่าสุด</li>
          <li>ตัวละครหลักสองคนที่เล่นได้</li>
          <li>เนื้อเรื่องที่ลึกซึ้งและซับซ้อน</li>
        </ul>

        <h3>แพลตฟอร์มที่รองรับ</h3>
        <p>GTA 6 จะวางจำหน่ายบน PlayStation 5 และ Xbox Series X/S ในช่วงแรก โดยเวอร์ชัน PC คาดว่าจะตามมาในภายหลัง ตามแบบฉบับของ Rockstar Games</p>
      `
        },
        {
            id: 4,
            title: 'Call of Duty เปิดตัวกิจกรรม Double XP ใหม่ในเดือนกุมภาพันธ์ 2025',
            category: 'ข่าวสาร',
            date: '14 ธันวาคม 2567',
            author: 'Activision',
            readTime: '3 นาที',
            description: 'Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg',
            tags: ['Call of Duty', 'Event', 'Double XP'],
            content: `
        <h2>กิจกรรม Double XP พิเศษ</h2>
        <p>Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone ผู้เล่นมีเวลาจนถึงกลางเดือนกุมภาพันธ์ 2025 เพื่อใช้ประโยชน์จากโปรโมชัน Call of Duty ที่เพิ่งเริ่มต้น</p>

        <h3>รายละเอียดกิจกรรม</h3>
        <ul>
          <li>ระยะเวลา: ตั้งแต่วันนี้ - กลางเดือนกุมภาพันธ์ 2025</li>
          <li>โหมดที่ร่วมรายการ: Black Ops 6 และ Warzone</li>
          <li>รางวัล: Double XP สำหรับทุกโหมด</li>
          <li>เงื่อนไข: ไม่มีเงื่อนไขพิเศษ เล่นได้เลย</li>
        </ul>

        <h3>วิธีการเข้าร่วม</h3>
        <p>ผู้เล่นสามารถเข้าร่วมกิจกรรมได้ทันทีโดยไม่ต้องลงทะเบียนเพิ่มเติม เพียงแค่เข้าเล่นเกมตามปกติ ระบบจะคำนวณ XP ที่ได้รับเป็น 2 เท่าโดยอัตโนมัติ</p>
      `
        },
        {
            id: 5,
            title: 'GTA 6 Release Date Still Set for Fall 2025',
            category: 'ข่าวสาร',
            date: '13 ธันวาคม 2567',
            author: 'Rockstar Games',
            readTime: '4 นาที',
            description: 'ตามรายงานผลประกอบการทางการเงินของ Take-Two ที่เกิดขึ้นเมื่อวันนี้ บริษัทแม่มั่นใจว่า GTA 6 จะออกวางจำหน่ายในฤดูใบไม้ร่วงปี 2025',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg',
            tags: ['GTA 6', 'Release Date', 'Rockstar'],
            content: `
        <h2>ยืนยันวันวางจำหน่าย GTA 6</h2>
        <p>ตามรายงานผลประกอบการทางการเงินของ Take-Two ที่เกิดขึ้นเมื่อวันนี้ ณ เวลาที่บันทึกข้อมูลนี้ บริษัทแม่มั่นใจว่า GTA 6 จะออกวางจำหน่ายในฤดูใบไม้ร่วงปี 2025 นั่นหมายความว่าข่าวลือเรื่องการเลื่อนกำหนดวางจำหน่ายเป็นเพียงข่าวลือเท่านั้น</p>

        <h3>สิ่งที่คาดหวังได้</h3>
        <ul>
          <li>โลกเปิดที่ใหญ่ที่สุดในประวัติศาสตร์ GTA</li>
          <li>กราฟิกที่สมจริงด้วยเทคโนโลยีล่าสุด</li>
          <li>ตัวละครหลักสองคนที่เล่นได้</li>
          <li>เนื้อเรื่องที่ลึกซึ้งและซับซ้อน</li>
        </ul>

        <h3>แพลตฟอร์มที่รองรับ</h3>
        <p>GTA 6 จะวางจำหน่ายบน PlayStation 5 และ Xbox Series X/S ในช่วงแรก โดยเวอร์ชัน PC คาดว่าจะตามมาในภายหลัง ตามแบบฉบับของ Rockstar Games</p>
      `
        },
        {
            id: 6,
            title: 'Call of Duty เปิดตัวกิจกรรม Double XP ใหม่ในเดือนกุมภาพันธ์ 2025',
            category: 'ข่าวสาร',
            date: '14 ธันวาคม 2567',
            author: 'Activision',
            readTime: '3 นาที',
            description: 'Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg',
            tags: ['Call of Duty', 'Event', 'Double XP'],
            content: `
        <h2>กิจกรรม Double XP พิเศษ</h2>
        <p>Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone ผู้เล่นมีเวลาจนถึงกลางเดือนกุมภาพันธ์ 2025 เพื่อใช้ประโยชน์จากโปรโมชัน Call of Duty ที่เพิ่งเริ่มต้น</p>

        <h3>รายละเอียดกิจกรรม</h3>
        <ul>
          <li>ระยะเวลา: ตั้งแต่วันนี้ - กลางเดือนกุมภาพันธ์ 2025</li>
          <li>โหมดที่ร่วมรายการ: Black Ops 6 และ Warzone</li>
          <li>รางวัล: Double XP สำหรับทุกโหมด</li>
          <li>เงื่อนไข: ไม่มีเงื่อนไขพิเศษ เล่นได้เลย</li>
        </ul>

        <h3>วิธีการเข้าร่วม</h3>
        <p>ผู้เล่นสามารถเข้าร่วมกิจกรรมได้ทันทีโดยไม่ต้องลงทะเบียนเพิ่มเติม เพียงแค่เข้าเล่นเกมตามปกติ ระบบจะคำนวณ XP ที่ได้รับเป็น 2 เท่าโดยอัตโนมัติ</p>
      `
        }
    ];

    constructor(
        private route: ActivatedRoute,
        private router: Router
    ) { }

    ngOnInit() {
        this.route.params.subscribe(params => {
            this.newsId = +params['id'];
            this.loadNewsDetail();
            this.loadRelatedNews();
        });
    }

    loadNewsDetail() {
        this.newsItem = this.allNews.find(news => news.id === this.newsId) || null;
        if (!this.newsItem) {
            // ถ้าไม่เจอข่าว ให้กลับไปหน้ารายการข่าว
            this.router.navigate(['/news']);
        }
    }

    loadRelatedNews() {
        // แสดงข่าวอื่นๆ ที่ไม่ใช่ข่าวปัจจุบัน (สูงสุด 3 ข่าว)
        this.relatedNews = this.allNews
            .filter(news => news.id !== this.newsId)
            .slice(0, 3);
    }

    goBack() {
        this.router.navigate(['/news']);
    }

    shareOnFacebook() {
        // Placeholder for Facebook share
        console.log('Share on Facebook');
    }

    shareOnTwitter() {
        // Placeholder for Twitter share
        console.log('Share on Twitter');
    }

    copyLink() {
        // Copy current URL to clipboard
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            alert('ลิงก์ถูกคัดลอกแล้ว!');
        });
    }
}
