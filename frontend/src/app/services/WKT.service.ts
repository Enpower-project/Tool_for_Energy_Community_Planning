import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class WKTService {

    constructor() { }

    public CoordsToWKT(type: any, coordinates: any): string {

        switch (type) {
            case 'Point':
                return `POINT(${coordinates.join(' ')})`;

            case 'LineString':
                return `LINESTRING(${coordinates.map((coord: number[]) => coord.join(' ')).join(', ')})`;

            case 'Polygon':
                return `POLYGON(${coordinates.map((ring: number[][]) =>
                    `(${ring.map((coord: number[]) => coord.join(' ')).join(', ')})`
                ).join(', ')})`;

            case 'MultiPoint':
                return `MULTIPOINT(${coordinates.map((point: number[]) => `(${point.join(' ')})`).join(', ')})`;

            case 'MultiLineString':
                return `MULTILINESTRING(${coordinates.map((line: number[][]) =>
                    `(${line.map((coord: number[]) => coord.join(' ')).join(', ')})`
                ).join(', ')})`;

            case 'MultiPolygon':
                return `MULTIPOLYGON(${coordinates.map((polygon: number[][][]) =>
                    `(${polygon.map((ring: number[][]) =>
                        `(${ring.map((coord: number[]) => coord.join(' ')).join(', ')})`
                    ).join(', ')})`
                ).join(', ')})`;

            default:
                throw new Error(`Unsupported geometry type: ${type}`);
        }
    }

    public WktToCoords(type: any, coordinates: string) {
        if (coordinates) {
            return coordinates?.replace(`${type} (`, '')?.replace(`${type}(`, '')?.replace(')', '')?.split(' ');
        }
        return "";
    }

    public WktToCoordsPolygon(type: any, coordinates: string) {
        const coordinatesText = coordinates
            .replace(`${type}((`, '')
            .replace(`${type} ((`, '')
            .replace('))', '');

        const coords = coordinatesText.split(', ').map(coord => {
            const [lng, lat] = coord.split(' ').map(Number);
            return [lat, lng] as [number, number];
        });

        return coords

    }

    // public WktToCoordsMultiPolygon(type: any, coordinates: string) {
    //     const coordinatesText = coordinates
    //         .replace(`${type}`, '')
    //         .replace(`${type} `, '')
    //         .replaceAll(`(`, '')
    //         .replaceAll(')', '');

    //     const coords = coordinatesText.split(', ').map(coord => {
    //         const [lng, lat] = coord.split(' ').map(Number);
    //         return [lat, lng] as [number, number];
    //     });

    //     return coords

    // }

    public WktToCoordsMultiPolygon(wkt: string): number[][][] {
        const coordinatesText = wkt
            .replace('MULTIPOLYGON (((', '') 
            .replace('MULTIPOLYGON(((', '') 
            .replace(')))', ''); 
    
        const coordinates = coordinatesText.split(',').map(coord => {
            const [longitude, latitude] = coord.trim().split(' ').map(Number);
            return [latitude, longitude]; 
        });
    
        return [coordinates];
    }
}