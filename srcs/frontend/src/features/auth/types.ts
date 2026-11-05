export interface TokenResponse {
	access_token: string;
	token_type: "Bearer";
}

export interface Account {
	id: string;
	email: string;
	created_at: string; // data given by the backend for the getMe (get account)
}
