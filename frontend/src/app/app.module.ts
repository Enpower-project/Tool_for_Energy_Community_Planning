import { APP_INITIALIZER, NgModule, isDevMode } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HomeComponent } from './components/home/home.component';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { HTTP_INTERCEPTORS, HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { StepsStructureComponent } from './components/formulary/steps-structure/steps-structure.component';
import { NumberSelectorComponent } from './components/formulary/number-selector/number-selector.component';
import { StepsComponent } from './components/formulary/steps/steps.component';
import { SliderComponentComponent } from './components/formulary/slider-component/slider-component.component';
import { ModalComponent } from './components/basic-components/modal/modal.component';
import { CardSelectorComponent } from './components/formulary/card-selector/card-selector.component';
import { WelcomeSelectorComponent } from './components/welcome-selector/welcome-selector.component';
import { FaqComponent } from './components/faq/faq.component';
import { DropdownComponent } from './components/basic-components/dropdown/dropdown.component';
import { AddressSelectorComponent } from './components/formulary/address-selector/address-selector.component';
import { AlertMessagesComponent } from './components/basic-components/alert-messages/alert-messages.component';
import { SelectComponent } from './components/basic-components/select/select.component';
import { StepperComponent } from './components/basic-components/stepper/stepper.component';
import { BuildingSelectorComponent } from './components/formulary/building-selector/building-selector.component';
import { SliderComponent } from './components/basic-components/slider/slider.component';
import { NumberInputComponent } from './components/basic-components/number-input/number-input.component';
import { MultipleSelectComponent } from './components/basic-components/multiple-select/multiple-select.component';
import { CommunityDemoComponent } from './components/formulary/community-demo/community-demo.component';
import { HorizontalMenuComponent } from './components/basic-components/horizontal-menu/horizontal-menu.component';
import { KeycloakService, KeycloakAngularModule } from 'keycloak-angular';
import { TokenInterceptor } from './components/AuthGuard/RefreshToken/TokenInterceptor';
import { HeaderHomeComponent } from './components/home/header-home/header-home.component';
import { BenefitsSelectorComponent } from './components/formulary/benefits-selector/benefits-selector.component';
import { RecommendedActionsComponent } from './components/formulary/recommended-actions/recommended-actions.component';
import { FindCommunitySelectorComponent } from './components/formulary/find-community-selector/find-community-selector.component';
import { LoadingComponent } from './components/basic-components/loading/loading.component';
import { InputTextComponent } from './components/basic-components/input-text/input-text.component';
import { KnowldedgeCentreComponent } from './components/knowldedge-centre/knowldedge-centre.component';
import { ScenarioComponentComponent } from './components/formulary/scenario-component/scenario-component.component';
import { CardDropdownComponent } from './components/basic-components/card-dropdown/card-dropdown.component';
import { KpiCardComponent } from './components/basic-components/kpi-card/kpi-card.component';
import { SeparatorComponent } from './components/basic-components/separator/separator.component';
import { BasicCardComponent } from './components/basic-components/basic-card/basic-card.component';
import { OurCommunityComponent } from './components/formulary/our-community/our-community.component';
import { AutocompleteComponent } from './components/basic-components/autocomplete/autocomplete.component';
import { ProgressBarComponent } from './components/basic-components/progress-bar/progress-bar.component';
import { PreventContextMenuDirective } from './directives/PreventContextMenu.directive';
import { SidebarComponent } from './components/basic-components/sidebar/sidebar.component';
import { NavigationControlerComponent } from './components/basic-components/navigation-controler/navigation-controler.component';
import { VerticalStepperComponent } from './components/basic-components/vertical-stepper/vertical-stepper.component';
import { LangSelectorComponent } from './components/basic-components/lang-selector/lang-selector.component';
import { AlertsComponent } from './components/alerts/alerts.component';
import { ServiceWorkerModule } from '@angular/service-worker';
import { AlternativesComponent } from './components/formulary/alternatives/alternatives.component';
import { RefineCommunityComponent } from './components/formulary/refine-community/refine-community.component';
import { OurAlternativesComponent } from './components/formulary/our-alternatives/our-alternatives.component';
import { CardImageComponent } from './components/basic-components/card-image/card-image.component';
import { BadgeComponent } from './components/basic-components/badge/badge.component';
import { CarrouselComponent } from './components/basic-components/carrousel/carrousel.component';
import { KpiModalComponent } from './components/basic-components/kpi-modal/kpi-modal.component';
import { NgxEchartsModule } from 'ngx-echarts';
import { CompareComponent } from './components/formulary/compare/compare.component';
import { LimitWordsPipe } from './pipes/limit-words.pipe';
import { BuildingAdvancedComponent } from './components/formulary/building-selector/building-advanced/building-advanced.component';
import { IconComponent } from './components/basic-components/icon/icon.component';

export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

export function initializeKeycloak(keycloak: KeycloakService) {
  return () => {
    return keycloak.init({
      config: {
        url: 'https://tools.cartif.es/auth_v25',
        realm: 'enpower',
        clientId: 'enpower_frontend',
      },
      shouldUpdateToken(request) {
        return !request.headers.get('token-update') === true;
      },
      
      initOptions: {
        onLoad: 'check-sso',
      },

    }).then(() => {
      console.info("Keycloak initialized successfully.");
    }).catch(error => {
      console.error("Error initializing Keycloak:", error);
    });
  };
}

@NgModule({ declarations: [
        AppComponent,
        HomeComponent,
        HeaderHomeComponent,
        NumberSelectorComponent,
        SliderComponentComponent,
        StepsComponent,
        StepsStructureComponent,
        ModalComponent,
        CardSelectorComponent,
        WelcomeSelectorComponent,
        FaqComponent,
        DropdownComponent,
        AddressSelectorComponent,
        AlertMessagesComponent,
        SelectComponent,
        StepperComponent,
        BuildingSelectorComponent,
        SliderComponent,
        NumberInputComponent,
        MultipleSelectComponent,
        CommunityDemoComponent,
        HorizontalMenuComponent,
        BenefitsSelectorComponent,
        RecommendedActionsComponent,
        FindCommunitySelectorComponent,
        LoadingComponent,
        InputTextComponent,
        KnowldedgeCentreComponent,
        ScenarioComponentComponent,
        CardDropdownComponent,
        KpiCardComponent,
        SeparatorComponent,
        BasicCardComponent,
        OurCommunityComponent,
        AutocompleteComponent,
        ProgressBarComponent,
        PreventContextMenuDirective,
        SidebarComponent,
        NavigationControlerComponent,
        VerticalStepperComponent,
        LangSelectorComponent,
        AlertsComponent,
        AlternativesComponent,
        RefineCommunityComponent,
        OurAlternativesComponent,
        CardImageComponent,
        BadgeComponent,
        CarrouselComponent,
        KpiModalComponent,
        CompareComponent,
        LimitWordsPipe,
        BuildingAdvancedComponent,
        IconComponent
    ],
    bootstrap: [AppComponent], imports: [TranslateModule.forRoot({
            defaultLanguage: 'en',
            loader: {
                provide: TranslateLoader,
                useFactory: HttpLoaderFactory,
                deps: [HttpClient]
            },
        }),
        BrowserModule,
        AppRoutingModule,
        ReactiveFormsModule,
        FormsModule,
        KeycloakAngularModule,
        ServiceWorkerModule.register('ngsw-worker.js', {
            enabled: !isDevMode(),
            // Register the ServiceWorker as soon as the application is stable
            // or after 30 seconds (whichever comes first).
            registrationStrategy: 'registerWhenStable:30000'
        }),
        NgxEchartsModule.forRoot({
            /**
             * This will import all modules from echarts.
             * If you only need custom modules,
             * please refer to [Custom Build] section.
             */
            echarts: () => import('echarts'), // or import('./path-to-my-custom-echarts')
        })], providers: [
        {
            provide: APP_INITIALIZER,
            useFactory: initializeKeycloak,
            multi: true,
            deps: [KeycloakService]
        },
        {
            provide: HTTP_INTERCEPTORS,
            useClass: TokenInterceptor,
            multi: true,
        },
        provideHttpClient(withInterceptorsFromDi()),
    ] })
export class AppModule { }
