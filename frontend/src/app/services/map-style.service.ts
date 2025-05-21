import { Injectable } from '@angular/core';

/**
 * Map building style service
 *
 * @export
 * @class MapStyleService
 * @typedef {MapStyleService}
 */
@Injectable({
  providedIn: 'root'
})
export class MapStyleService {

  /**
   * Creates an instance of MapStyleService.
   *
   * @constructor
   */
  constructor() { }

  /**
   * Returns the specific color by type
   *
   * @param {("disabled" | "selected" | "basic")} type
   * @returns {{ weight: number; color: string; fillColor: string; }}
   */
  getBuildingColor(type: "disabled" | "selected" | "basic") {

    if (type === "disabled") {
      return {
        weight: 4,
        color: "#71717A",
        fillColor: '#71717A'
      }
    }

    if (type === "basic") {
      return {
        weight: 3,
        color: "#3B62AB",
        fillColor: '#3B62AB'
      }
    }

    if (type === "selected") {
      return {
        weight: 4,
        color: "#4CB689",
        fillColor: '#4CB689'
      }
    }

    return {
      weight: 3,
      color: "#3B62AB",
      fillColor: '#3B62AB'
    }
  }

}
