## Endpoints

GET		/api/personalization/profiles/{profile_id}
GET		/api/personalization/profiles (to have the list of users for friends)
UPDATE	/api/personalization/profiles/{profile_id}

GET		/api/personalization/profile/saved-articles
POST	/api/personalization/profile/saved-articles/{id}
DELETE	/api/personalization/profile/saved-articles/{id}

## Profile
```Text

GET /api/personalization/profiles/{profile_id}
Body: {}
Header:
	Authorization: Bearer XXXX
Response:
	- 200 OK
	{
		display_name: str,
		interests: list[str],
		avatar:
	}
	- 404 Not Found

--------------------
UPDATE /api/personalization/profile/{profile_id}
Body:
{
	display_name: str,
	interests: list[str],
	avatar:
}
Header:
	Authorization: Bearer XXXX
Response:
	-
	-
```

## Saved_articles
```Text
GET /api/personalization/profiles/saved_articles
Body:
{

}
Header:

	Authorization: Bearer XXXX
Response:
	-
	-

---------------------
POST /api/personalization/profiles/saved_article/{id}
Body:
{

}
Header:
	Authorization: Bearer XXXX
Response:
	-
	-

```