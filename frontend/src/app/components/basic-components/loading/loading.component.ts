import { Component, Input } from '@angular/core';

/**
 * Custom loading 
 *
 * @export
 * @class LoadingComponent
 * @typedef {LoadingComponent}
 */
@Component({
  selector: 'loading',
  templateUrl: './loading.component.html',
  styleUrls: ['./loading.component.scss']
})
export class LoadingComponent {

  /**
   * Valid if show the loading
   *
   * @type {boolean}
   */
  @Input() show: boolean = false;
  /**
   * Change if the modal have the position absolute or fixed 
   *
   * @type {boolean}
   */
  @Input() isAbsolute: boolean = false;

  @Input() withBackground: boolean = true;

  /**
   * Creates an instance of LoadingComponent.
   *
   * @constructor
   */
  constructor() { }

}
