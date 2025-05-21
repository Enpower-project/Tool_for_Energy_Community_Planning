import { Component, OnInit, OnDestroy } from '@angular/core';
import { interval, Subscription } from 'rxjs';
interface Wine {
  image: string;
  name: string;
  description: string;
}


@Component({
  selector: 'carrousilitups',
  templateUrl: './carrousel.component.html',
  styleUrls: ['./carrousel.component.scss']
})
export class CarrouselComponent implements OnInit {
  numberItems: number[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
  currentNumberIndex: number = 0;

  numberCarouselSubscription!: Subscription;

  itemsToShow: number = 1;

  constructor() { }

  ngOnInit(): void {
    this.updateItemsToShow();
    window.addEventListener('resize', this.updateItemsToShow.bind(this));
  }

  ngOnDestroy(): void {
    if (this.numberCarouselSubscription) {
      this.numberCarouselSubscription.unsubscribe();
    }
    window.removeEventListener('resize', this.updateItemsToShow.bind(this));
  }

  updateItemsToShow(): void {
    const width = window.innerWidth;
    if (width >= 1400) {
      this.itemsToShow = 6;
    } else if (width >= 810) {
      this.itemsToShow = 4;
    } else if (width >= 620) {
      this.itemsToShow = 3;
    } else if (width >= 480) {
      this.itemsToShow = 2;
    } else {
      this.itemsToShow = 1;
    }
  }

  prevNumber(): void {
    this.currentNumberIndex = (this.currentNumberIndex - this.itemsToShow + this.numberItems.length) % this.numberItems.length;
  }

  nextNumber(): void {
    this.currentNumberIndex = (this.currentNumberIndex + this.itemsToShow) % this.numberItems.length;
  }

  startAutoSlide(): void {
    const intervalTime = 3000; 
    this.numberCarouselSubscription = interval(intervalTime).subscribe(() => {
      this.nextNumber();
    });
  }

  getNumberTransform(): string {
    const itemWidth = 200 + 10; 
    const offset = -this.currentNumberIndex * itemWidth;
    return `translateX(${offset}px)`;
  }

}