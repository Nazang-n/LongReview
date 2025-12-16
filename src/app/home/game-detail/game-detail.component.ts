import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { ProgressBarModule } from 'primeng/progressbar';
import { TextareaModule } from 'primeng/textarea';

interface Review {
    id: number;
    username: string;
    rating: number;
    date: string;
    content: string;
    helpful: number;
}

interface RelatedGame {
    id: number;
    title: string;
    image: string;
    date: string;
    tags: string[];
    reviewTags: string[];
}

@Component({
    selector: 'app-game-detail',
    standalone: true,
    imports: [
        CommonModule,
        HeaderComponent,
        FooterComponent,
        RouterModule,
        TagModule,
        ButtonModule,
        CardModule,
        ProgressBarModule,
        TextareaModule
    ],
    templateUrl: './game-detail.component.html',
    styleUrls: ['./game-detail.component.css']
})
export class GameDetailComponent implements OnInit {
    @ViewChild('reviewsContainer') reviewsContainer!: ElementRef;

    gameId: string | null = '';

    game = {
        title: 'Armored Core VI: Fires of Rubicon',
        image: 'https://cdn.akamai.steamstatic.com/steam/apps/1938090/header.jpg',
        tags: ['แอ็คชั่น', 'เมคคา', 'ผู้เล่นคนเดียว'],
        releaseDate: '25 ส.ค. 2566',
        developer: 'FromSoftware Inc.',
        publisher: 'BANDAI NAMCO Entertainment',
        platform: 'Steam, PS5, Xbox Series',
        description: `เกมแอ็คชั่นเมคคาสุดมันส์จาก FromSoftware ผู้สร้าง Dark Souls และ Elden Ring กลับมาพร้อมกับซีรีส์ Armored Core ที่หายไปนาน 10 ปี ในภาคนี้คุณจะได้สวมบทเป็นนักรบเมคคาที่ต้องต่อสู้เพื่อความอยู่รอดบนดาวเคราะห์ Rubicon 3 ที่เต็มไปด้วยสงครามและความขัดแย้ง

ระบบการต่อสู้ที่รวดเร็วและเข้มข้น พร้อมระบบปรับแต่งเมคคาที่ลึกซึ้ง ให้คุณสร้างหุ่นรบในแบบของคุณเอง`,
        score: 77,
        ratings: {
            excellent: 77,
            good: 15,
            average: 5,
            poor: 3
        },
        sentiment: {
            positive: 82,
            neutral: 12,
            negative: 6
        },
        reviewTags: [
            { label: 'ท้าทาย', count: 1250, severity: 'warning' },
            { label: 'ยาก', count: 980, severity: 'danger' },
            { label: 'สนุก', count: 2100, severity: 'success' },
            { label: 'กราฟิกสวย', count: 1800, severity: 'info' },
            { label: 'ควบคุมยาก', count: 650, severity: 'warning' },
            { label: 'คุ้มค่า', count: 1500, severity: 'success' }
        ],
        minRequirements: '2,250 THB'
    };

    reviews: Review[] = [
        {
            id: 1,
            username: 'User01',
            rating: 5,
            date: '15 ก.ย. 2567',
            content: 'เกมแอ็คชั่นเมคคาที่ดีที่สุดในรอบหลายปี! ระบบการปรับแต่งเมคคาลึกซึ้งมาก การต่อสู้สนุกและท้าทาย กราฟิกสวยงาม เหมาะกับคนที่ชอบเกมแนว Souls-like และเมคคา',
            helpful: 125
        },
        {
            id: 2,
            username: 'User02',
            rating: 4,
            date: '3 ก.ย. 2567',
            content: 'เกมสนุกดี แต่ความยากค่อนข้างสูงสำหรับมือใหม่ ต้องใช้เวลาในการเรียนรู้ระบบการควบคุมและการปรับแต่งเมคคา แต่พอเข้าใจแล้วก็สนุกมาก',
            helpful: 89
        },
        {
            id: 3,
            username: 'Duck',
            rating: 5,
            date: '8 ส.ค. 2567',
            content: 'FromSoftware ทำได้ดีอีกแล้ว! เนื้อเรื่องน่าสนใจ ระบบการต่อสู้ลื่นไหล และมีเนื้อหาให้เล่นเยอะมาก คุ้มค่ากับราคาแน่นอน',
            helpful: 203
        },
        {
            id: 4,
            username: 'Dug',
            rating: 4,
            date: '1 ส.ค. 2567',
            content: 'กราฟิกสวยงาม เสียงเพลงเข้ากับบรรยากาศ แต่บางภารกิจยากเกินไปจนต้องลองหลายรอบ โดยรวมแล้วเป็นเกมที่ดีมาก',
            helpful: 156
        },
        {
            id: 5,
            username: 'GameZ3',
            rating: 5,
            date: '27 ก.ค. 2567',
            content: 'รอมานานและไม่ผิดหวัง! ระบบการปรับแต่งเมคคามีความหลากหลายมาก สามารถสร้างสไตล์การเล่นของตัวเอง Boss fight ท้าทายและสนุกทุกตัว',
            helpful: 178
        }
    ];

    relatedGames: RelatedGame[] = [
        {
            id: 101,
            title: 'Lies of P',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1627720/header.jpg',
            date: '19 ก.ย. 2566',
            tags: ['แอ็คชั่น', 'RPG'],
            reviewTags: ['ท้าทาย', 'สวยงาม']
        },
        {
            id: 102,
            title: 'DAEMON X MACHINA',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1167450/header.jpg',
            date: '13 ก.พ. 2563',
            tags: ['แอ็คชั่น', 'เมคคา'],
            reviewTags: ['สนุก', 'ปรับแต่งได้']
        },
        {
            id: 103,
            title: 'Elden Ring',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg',
            date: '25 ก.พ. 2565',
            tags: ['แอ็คชั่น', 'RPG'],
            reviewTags: ['ยาก', 'คุ้มค่า']
        },
        {
            id: 104,
            title: 'METAL GEAR RISING: REVENGEANCE',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/235460/header.jpg',
            date: '9 ม.ค. 2557',
            tags: ['แอ็คชั่น', 'เมคคา'],
            reviewTags: ['มันส์', 'เพลงเพราะ']
        }
    ];

    displayedReviewsCount = 3; // Initially show 3 reviews

    constructor(private route: ActivatedRoute) { }

    ngOnInit() {
        this.gameId = this.route.snapshot.paramMap.get('id');
    }

    getRatingIcon(rating: number): string {
        return rating >= 4 ? 'pi-thumbs-up' : rating >= 3 ? 'pi-minus' : 'pi-thumbs-down';
    }

    getRatingColor(rating: number): string {
        return rating >= 4 ? 'text-green-600' : rating >= 3 ? 'text-yellow-600' : 'text-red-600';
    }

    scrollReviews(direction: 'left' | 'right') {
        const container = this.reviewsContainer.nativeElement;
        const scrollAmount = 400; // Width of one card (384px) plus gap

        if (direction === 'left') {
            container.scrollLeft -= scrollAmount;
        } else {
            container.scrollLeft += scrollAmount;
        }
    }

    loadMoreReviews() {
        this.displayedReviewsCount += 3; // Load 3 more reviews each time
    }
}
