import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';

interface NewsItem {
    id: number;
    title: string;
    category?: string;
    date?: string;
    description?: string;
    image: string;
}

@Component({
    selector: 'app-news',
    standalone: true,
    imports: [CommonModule, HeaderComponent, FooterComponent, ButtonModule, CardModule, TagModule, DividerModule],
    templateUrl: './news.component.html',
    styleUrls: ['./news.component.css']
})
export class NewsComponent {
    featuredNews: NewsItem = {
        id: 1,
        title: 'Path of exile 2 2.0.1',
        description: 'บททดสอบแห่งเช็คเคมา ผู้เล่นไม่พอใจกับการเผชิญกับบททดสอบแห่งเช็คเคมาโดยเฉพาะในการต่อสู้ระยะใกล้ เราจึงปรับวิธีคำนวณความเสียหายที่เกิดขึ้นกับเกียรติเมื่ออยู่ในระยะใกล้ และทำการแก้ไขบัคที่สำคัญที่ทำให้ผู้เล่นได้รับความเสียหายต่อเกียรติมากเกินไปจากความเสียหายต่อเนื่อง',
        image: 'https://cdn.akamai.steamstatic.com/steam/apps/2694490/header.jpg'

    };

    sideNews: NewsItem[] = [
        {
            id: 2,
            title: 'Call of Duty เปิดตัวกิจกรรม Double XP ใหม่ในเดือนกุมภาพันธ์ 2025',
            description: 'ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg'
        },
        {
            id: 3,
            title: 'GTA 6 Release Date Still Set for Fall 2025',
            description: 'GTA 6 จะออกวางจำหน่ายในฤดูใบไม้ร่วงปี 2025',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg'
        }
    ];

    latestNews: NewsItem[] = [
        {
            id: 4,
            title: 'Call of Duty เปิดตัวกิจกรรม Double XP ใหม่ในเดือนกุมภาพันธ์ 2025',
            description: 'Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone ผู้เล่นมีเวลาจนถึงกลางเดือนกุมภาพันธ์ 2025 เพื่อใช้ประโยชน์จากโปรโมชัน Call of Duty ที่เพิ่งเริ่มต้น',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg'
        },
        {
            id: 5,
            title: 'GTA 6 Release Date Still Set for Fall 2025',
            description: 'ตามรายงานผลประกอบการทางการเงินของ Take-Two ที่เกิดขึ้นเมื่อวันนี้ ณ เวลาที่บันทึกข้อมูลนี้ บริษัทแม่มั่นใจว่า GTA 6 จะออกวางจำหน่ายในฤดูใบไม้ร่วงปี 2025 นั่นหมายความว่าข่าวลือเรื่องการเลื่อนกำหนดวางจำหน่ายเป็นเพียงข่าวลือเท่านั้น',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg'
        },
        {
            id: 6,
            title: 'Call of Duty เปิดตัวกิจกรรม Double XP ใหม่ในเดือนกุมภาพันธ์ 2025',
            description: 'Call of Duty ได้เปิดตัวกิจกรรม Double XP ใหม่ ซึ่งตอนนี้ให้เล่นทั้งใน Black Ops 6 และ Warzone ผู้เล่นมีเวลาจนถึงกลางเดือนกุมภาพันธ์ 2025 เพื่อใช้ประโยชน์จากโปรโมชัน Call of Duty ที่เพิ่งเริ่มต้น',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg'
        }
    ];
}
