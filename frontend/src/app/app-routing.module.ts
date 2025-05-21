import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { StepsComponent } from './components/formulary/steps/steps.component';
import { APP_ROUTES } from './data/routes';
import { WelcomeSelectorComponent } from './components/welcome-selector/welcome-selector.component';
import { FaqComponent } from './components/faq/faq.component';
import { CanDeactivateGuard } from './services/can-deactivate.guard';
import { KnowldedgeCentreComponent } from './components/knowldedge-centre/knowldedge-centre.component';
import { OurCommunityComponent } from './components/formulary/our-community/our-community.component';
import { AlternativesComponent } from './components/formulary/alternatives/alternatives.component';
import { RefineCommunityComponent } from './components/formulary/refine-community/refine-community.component';
import { OurAlternativesComponent } from './components/formulary/our-alternatives/our-alternatives.component';

const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: APP_ROUTES.HOME, component: HomeComponent },
  { path: APP_ROUTES.FORMULARY, component: StepsComponent, canDeactivate: [CanDeactivateGuard] },
  { path: APP_ROUTES.FORMULARY + '/:id', component: StepsComponent, canDeactivate: [CanDeactivateGuard] },
  { path: APP_ROUTES.WELCOME, component: WelcomeSelectorComponent },
  { path: APP_ROUTES.FAQ, component: FaqComponent },
  { path: APP_ROUTES.KNOWLDEDGE, component: KnowldedgeCentreComponent },
  { path: APP_ROUTES.COMMUNITY + '/:id', component: OurCommunityComponent },
  { path: APP_ROUTES.COMMUNITY + '/:id' + "/" + APP_ROUTES.REFINE, component: RefineCommunityComponent },
  { path: APP_ROUTES.COMMUNITY + '/:id' + '/' + APP_ROUTES.ALTERNATIVES + '/:id', component: OurAlternativesComponent },
  { path: APP_ROUTES.COMMUNITY + '/:id' + '/' + APP_ROUTES.ALTERNATIVE + '/:id', component: OurCommunityComponent },
  { path: APP_ROUTES.COMMUNITY + '/:id' + '/' + APP_ROUTES.ALTERNATIVES, component: AlternativesComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
