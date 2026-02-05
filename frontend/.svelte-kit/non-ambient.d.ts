
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/contacts" | "/documents" | "/documents/invoice" | "/documents/letter" | "/documents/offer";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/contacts": Record<string, never>;
			"/documents": Record<string, never>;
			"/documents/invoice": Record<string, never>;
			"/documents/letter": Record<string, never>;
			"/documents/offer": Record<string, never>
		};
		Pathname(): "/" | "/contacts" | "/contacts/" | "/documents" | "/documents/" | "/documents/invoice" | "/documents/invoice/" | "/documents/letter" | "/documents/letter/" | "/documents/offer" | "/documents/offer/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}