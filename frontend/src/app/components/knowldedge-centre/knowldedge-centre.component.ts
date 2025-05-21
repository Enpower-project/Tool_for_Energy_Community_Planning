import { Component, OnInit } from '@angular/core';
import { NavigateService } from '../../services/navigate.service';
import { EXTERNAL_ROUTES } from '../../data/externalRoutes';
import { cardGlossaryArray, glossaryItems, UsefulResources } from '../../data/types';

@Component({
  selector: 'app-knowldedge-centre',
  templateUrl: './knowldedge-centre.component.html',
  styleUrls: ['./knowldedge-centre.component.scss']
})
export class KnowldedgeCentreComponent implements OnInit {

  public cardGlossaryArray = cardGlossaryArray;
  public initialLimit: number = 4;
  public limit: number = this.initialLimit;
  public textShowMore = 'SEE_MORE'
  public glossaryItems = glossaryItems;
  public selectedMenuGlossary: string = "ENERGY_COMMUNITIES";

  public usefulResources = UsefulResources;

  constructor(
    private navigateService: NavigateService
  ) { }

  ngOnInit() {
  }

  navigateMoreSites(name: string) {
    this.navigateService.openNewPage((EXTERNAL_ROUTES as any)[name])
  }

  navigateOtherSites(name?: string) {
    if (name)
      this.navigateService.openNewPage(name)
  }

  public showMoreOrLess() {
    this.limit = this.limit === this.initialLimit ? this.glossaryItems[this.selectedMenuGlossary].length : this.initialLimit;
    this.textShowMore = this.limit === this.initialLimit ? 'SEE_MORE' : 'SEE_LESS';
  }
}
