import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class NavigateService {

  constructor() { }

  /**
   * open an URL in a new page
   *
   * @public
   * @param {string} route
   */
  public openNewPage(route: string): void {
    window.open(route, '_blank');
  }

}
