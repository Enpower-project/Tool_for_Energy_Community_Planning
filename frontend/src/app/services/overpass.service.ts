import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class OverpassService {
  private overpassUrl = 'https://overpass-api.de/api/interpreter';

  constructor(private http: HttpClient) { }

  getBuildings(bbox: string): Observable<any> {

    const query = `[out:json][timeout:25];(way["building"](poly:"41.650942592498524 -4.720077019219509 41.65071017761873 -4.720291564804886 41.64988469730219 -4.719701564445118 41.65097464965752 -4.718135381671907 41.65166387471721 -4.719015018571928");relation["building"](poly:"41.650942592498524 -4.720077019219509 41.65071017761873 -4.720291564804886 41.64988469730219 -4.719701564445118 41.65097464965752 -4.718135381671907 41.65166387471721 -4.719015018571928"););out body;>;out skel qt;`;
    const params = new HttpParams().set('data', query);
    return this.http.get(this.overpassUrl, { params });
  }

  transformDataToGeoJSON(data: any): any {
    let features = [] as any;
    data.elements.forEach((el: any) => {
      if (el?.tags?.building === "yes") {
        features.push(
          {
            type: 'Feature',
            properties: el.tags,
            geometry: {
              type: 'Polygon',
              coordinates: this.getPolygonCoordinates(el)
            }
          }
        )
      }

    });

    return {
      type: 'FeatureCollection',
      features: features
    };
  }

  getPolygonCoordinates(el: any): any {
    return el?.nodes;
  }

  getBuildingsInBoundary(minLat: number, minLon: number, maxLat: number, maxLon: number): Observable<any> {
    const overpassUrl = 'https://overpass-api.de/api/interpreter';
    const query = `[out:json][timeout:25];
      (
        way["building"]
        (${minLat},${minLon},${maxLat},${maxLon});
        relation["building"]
        (${minLat},${minLon},${maxLat},${maxLon});
      );
      (._;>;);
      out body;`;

    return this.http.post(overpassUrl, `data=${encodeURIComponent(query)}`, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
  }

  public convertOsmToGeoJson(osmData: any): any {
    const geoJson = {
      type: "FeatureCollection",
      features: [] as any
    };

    osmData.elements.forEach((element: any) => {
      if (element.type === "way" && this.isPolygon(element.nodes)) {
        const coordinates = element.nodes.map((nodeId: any) => {
          const node = osmData.elements.find((e: any) => e.type === "node" && e.id === nodeId);
          return node ? [node.lon, node.lat] : null;
        }).filter((coord: any) => coord !== null);

        if (coordinates[0][0] !== coordinates[coordinates.length - 1][0] ||
          coordinates[0][1] !== coordinates[coordinates.length - 1][1]) {
          coordinates.push(coordinates[0]);
        }

        const properties = {
          tags: element.tags || {},
          id: element.id
        }

        geoJson.features.push({
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [coordinates]
          },
          properties: properties
        });
      }
    });

    return geoJson;
  }

  private isPolygon(nodeIds: number[]): boolean {
    if (!nodeIds || nodeIds.length < 4) return false;
    return nodeIds[0] === nodeIds[nodeIds.length - 1];
  }

}

