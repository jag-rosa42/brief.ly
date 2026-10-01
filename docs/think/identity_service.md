i am using this from fastapi

bearer_token_scheme = HTTPBearer()

AccessTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer_token_scheme)]



and my claims are structured thought this class:
class JWTTokenPayload(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_alias=True,
    )
    token_id: str = Field(alias="jti")
    subject: str = Field(alias="sub")
    token_type: TokenType = Field(alias="type")
    issued_at: int = Field(alias="iat")
    expires_at: int = Field(alias="exp")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JWTTokenPayload:
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise InvalidTokenError() from exc


and i use this lib: pyjwt[crypto]>=2.14.0"


here my full implementation:


class JWTTokenService:
    def __init__(self):
        self._private_key: SecretStr = settings.JWT_PRIVATE_KEY
        self._public_key: str = settings.JWT_PUBLIC_KEY
        self._algorithm: str = settings.JWT_ALGORITHM
        self._access_token_lifetime: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self._refresh_token_lifetime: timedelta = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    def create_access_token(self, account_id: UUID) -> str:
        created_token: CreatedToken = self._create_token(
            account_id,
            token_type=TokenType.ACCESS,
        )
        return created_token.token

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        payload: JWTTokenPayload = self._decode(token, expected_type=TokenType.ACCESS)

        account_id: UUID = self._parse_uuid(payload.subject)
        return AccessTokenClaims(
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def create_refresh_token(self, account_id: UUID) -> CreatedRefreshToken:
        refresh_token: CreatedToken = self._create_token(
            account_id,
            token_type=TokenType.REFRESH,
        )
        return CreatedRefreshToken(
            id=refresh_token.id,
            token=refresh_token.token,
            token_hash=self.hash_token(refresh_token.token),
            expires_at=refresh_token.expires_at,
        )

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims:
        payload: JWTTokenPayload = self._decode(token, expected_type=TokenType.REFRESH)

        token_id: UUID = self._parse_uuid(payload.token_id)
        account_id: UUID = self._parse_uuid(payload.subject)

        return RefreshTokenClaims(
            id=token_id,
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _create_token(self, account_id: UUID, token_type: TokenType) -> CreatedToken:
        now: datetime = datetime.now(UTC)
        token_id: UUID = uuid4()
        lifetime: timedelta = (
            self._access_token_lifetime
            if token_type == TokenType.ACCESS
            else self._refresh_token_lifetime
        )
        expires_at: datetime = now + lifetime
        payload: dict[str, Any] = {
            "jti": str(token_id),  # subject
            "sub": str(account_id),  # subject
            "type": token_type,
            "iat": now,  # Issued at
            "exp": expires_at,
        }
        token: str = jwt.encode(
            payload,
            self._private_key.get_secret_value(),
            self._algorithm,
        )
        return CreatedToken(id=token_id, token=token, expires_at=expires_at)

    def _decode(self, token: str, expected_type: TokenType) -> JWTTokenPayload:
        try:
            payload: dict[str, Any] = jwt.decode(
                jwt=token,
                key=self._public_key,
                algorithms=[self._algorithm],
                options={"require": ["sub", "type", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

        jwt_payload: JWTTokenPayload = JWTTokenPayload.from_dict(payload)
        if jwt_payload.token_type != expected_type:
            logger.debug("Unexpected token type: expected=%s", expected_type.value)
            raise InvalidTokenError()
        return jwt_payload

    def _parse_uuid(self, value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:
            raise InvalidTokenError() from exc


class CreateAccountSession:
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service

    def execute(self, account_id: UUID) -> AccountSession:
        access_token: str = self._token_service.create_access_token(account_id)
        created_refresh_token: CreatedRefreshToken = (
            self._token_service.create_refresh_token(account_id)
        )
        refresh_token = RefreshToken(
            id=created_refresh_token.id,
            account_id=account_id,
            token_hash=created_refresh_token.token_hash,
            expires_at=created_refresh_token.expires_at,
            created_at=datetime.now(UTC),
        )

        self._refresh_token_repository.add(refresh_token)

        return AccountSession(
            access_token=access_token,
            refresh_token=created_refresh_token.token,
            refresh_token_id=created_refresh_token.id,
        )

class RefreshAccountSession:
    def __init__(
        self,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._refresh_token_validator = refresh_token_validator
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, refresh_token: str) -> AccountSession:
        current_refresh_token = self._refresh_token_validator.get_valid_refresh_token(
            refresh_token
        )
        now: datetime = datetime.now(UTC)
        self._validate_refresh_token_state(current_refresh_token, now)
        new_account_session: AccountSession = self._create_account_session.execute(
            current_refresh_token.account_id
        )

        self._refresh_token_repository.flush()

        self._rotate_refresh_token(
            current_refresh_token=current_refresh_token,
            new_refresh_token_id=new_account_session.refresh_token_id,
            now=now,
        )
        self._refresh_token_repository.commit()

        return new_account_session

    def _validate_refresh_token_state(
        self,
        refresh_token: RefreshToken,
        now: datetime,
    ) -> None:
        if refresh_token.is_revoked():
            if refresh_token.was_rotated():
                self._refresh_token_repository.revoke_all_for_account(
                    refresh_token.account_id,
                    now,
                )
                self._refresh_token_repository.commit()
            raise TokenRevokedError()
        if refresh_token.is_expired(now):
            raise TokenExpiredError()

    def _rotate_refresh_token(
        self,
        current_refresh_token: RefreshToken,
        new_refresh_token_id: UUID,
        now: datetime,
    ) -> None:
        current_refresh_token.revoke(now, replaced_by=new_refresh_token_id)
        self._refresh_token_repository.update(current_refresh_token)

class RefreshTokenValidator:
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service

    def get_valid_refresh_token(self, refresh_token: str) -> RefreshToken:
                # Verify the JWT signature, claims, token type, etc.
        claims: RefreshTokenClaims = self._token_service.verify_refresh_token(
            refresh_token
        )

        # Find the database record corresponding to the JWT's `jti`.
        stored_token: RefreshToken | None = self._refresh_token_repository.find_by_id(
            claims.id,
        )

        # The database stores only the hash of the refresh token.
        # Hash the presented token and compare it with the stored hash.
        if (
            stored_token is None
            or stored_token.token_hash != self._token_service.hash_token(refresh_token)
        ):
            raise InvalidTokenError()
        return stored_token

class LoginAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, email: str, password: str) -> AccountSession:
        account: Account | None = self._account_repository.find_by_email(Email(email))
        if account is None:
            raise InvalidCredentialsError()
        if not self._password_hasher.verify(password, account.password_hash):
            raise InvalidCredentialsError()

        session: AccountSession = self._create_account_session.execute(account.id)
        self._account_repository.commit()

        return session

class LogoutAccount:
    def __init__(
        self,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self._refresh_token_validator: RefreshTokenValidator = refresh_token_validator
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository

    def execute(self, refresh_token: str) -> None:
        try:
            stored: RefreshToken = self._refresh_token_validator.get_valid_refresh_token(
                refresh_token
            )
        except (InvalidTokenError, TokenExpiredError):
            return

        if stored.is_revoked():
            return

        stored.revoke(datetime.now(UTC))
        self._refresh_token_repository.update(stored)
        self._refresh_token_repository.commit()


class RegisterAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, email: str, password: str) -> AccountSession:
        email_value_object: Email = Email(email)

        existing_account: Account | None = self._account_repository.find_by_email(
            email_value_object
        )

        if existing_account is not None:
            raise EmailAlreadyRegisteredError()

        password_hash: PasswordHash = self._password_hasher.hash(password)

        account: Account = Account(
            id=uuid4(),
            email=email_value_object,
            password_hash=password_hash,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        # TODO: Revisit the transaction boundary.
        # Currently, this use case explicitly commits/rolls back through the repository.
        # Consider moving transaction management to a Unit of Work or outer application
        # boundary so the entire use case is executed within a single transaction.
        try:
            self._account_repository.save(account)
            session: AccountSession = self._create_account_session.execute(account.id)
            self._account_repository.commit()
        except IntegrityError as exc:
            self._account_repository.rollback()
            raise EmailAlreadyRegisteredError() from exc
        except Exception:
            self._account_repository.rollback()
            raise

        return session

class GetCurrentAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        token_service: TokenService,
    ) -> None:
        self._accounts: AccountRepository = account_repository
        self._token_service: TokenService = token_service

    def execute(self, access_token: str) -> Account:
        claims: AccessTokenClaims = self._token_service.verify_access_token(
            access_token
        )
        account: Account | None = self._accounts.find_by_id(
            claims.account_id
        )
        if account is None:
            raise InvalidTokenError()
        return account


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountSessionResponse,
)
def register(
    body: RegisterRequest,
    register_account: RegisterAccountDep,
) -> AccountSessionResponse:
    session: AccountSession = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return AccountSessionResponse.from_session(session)


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=AccountSessionResponse,
)
def login(
    body: LoginRequest,
    login_account: LoginAccountDep,
) -> AccountSessionResponse:
    session: AccountSession = login_account.execute(
        email=body.email,
        password=body.password.get_secret_value(),
    )
    return AccountSessionResponse.from_session(session)


@router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    body: LogoutRequest,
    logout_account: LogoutAccountDep,
) -> None:
    logout_account.execute(body.refresh_token)


@router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AccountSessionResponse,
)
def refresh(
    body: RefreshRequest,
    refresh_account_session: RefreshAccountSessionDep,
) -> AccountSessionResponse:
    session: AccountSession = refresh_account_session.execute(body.refresh_token)
    return AccountSessionResponse.from_session(session)


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.get(
    path="/me",
    status_code=status.HTTP_200_OK,
    response_model=AccountResponse,
)
def get_me(current_account: CurrentAccountDep) -> AccountResponse:
    return AccountResponse.from_domain(current_account)
