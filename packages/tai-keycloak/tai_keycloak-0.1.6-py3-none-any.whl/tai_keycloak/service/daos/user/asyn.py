from typing import List, Optional
from keycloak import KeycloakAdmin
from ...dtos import User, OperationResult, KeycloakSDKException


class AsyncUserDAO:
    """DAO para operaciones CRUD de usuarios en Keycloak"""

    NAME = 'User'

    def __init__(self, client: KeycloakAdmin):
        self.client = client

    async def create(self, user: User) -> OperationResult[User]:
        """Crea un nuevo usuario"""
        try:
            user_data = user.model_dump(by_alias=True, exclude_none=True)
            
            # Remover campos que no se envían en la creación
            user_data.pop('id', None)

            user.id = await self.client.a_create_user(user_data, exist_ok=False)

            # Establecer contraseña si se proporciona
            if user.password:
                await self.client.a_set_user_password(user.id, user.password, temporary=False)

            return OperationResult(
                success=True,
                message=f"Usuario '{user.username}' creado exitosamente",
                data=user
            )

        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.create", f"usuario '{user.username}'")

    async def get(self, username: str) -> OperationResult[User]:
        """Obtiene un usuario por username"""
        try:
            user_id = await self.client.a_get_user_id(username)
            user_data = await self.client.a_get_user(user_id)
            user = User(**user_data)

            return OperationResult(
                success=True,
                message=f"Usuario '{username}' encontrado",
                data=user
            )

        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.get", f"usuario '{username}'")

    async def list(self) -> OperationResult[List[User]]:
        """Lista usuarios con filtros opcionales"""
        try:
            users = []
            for user_data in await self.client.a_get_users():
                users.append(User(**user_data))

            return OperationResult(
                success=True,
                message=f"Encontrados {len(users)} usuarios",
                data=users
            )
        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.list")

    async def update(self, user: User) -> OperationResult[User]:
        """Actualiza un usuario"""
        try:
            user_id = await self.client.a_get_user_id(user.username)
            await self.client.a_update_user(user_id, user.model_dump(exclude_unset=True))
            user.id = user_id
            return OperationResult(
                success=True,
                message=f'Usuario "{user.username}" actualizado exitosamente',
                data=user
            )
        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.update", f"usuario '{user.username}'")

    async def delete(self, username: str) -> OperationResult[None]:
        """Elimina un usuario"""
        try:
            user_id = await self.client.a_get_user_id(username)
            await self.client.a_delete_user(user_id)
            return OperationResult(
                success=True,
                message=f'Usuario "{username}" eliminado exitosamente'
            )
        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.delete", f"usuario '{username}'")

    async def add_to_group(self, username: str, group_name: str) -> OperationResult[None]:
        """Agrega un usuario a un grupo"""
        try:
            user_id = await self.client.a_get_user_id(username)
            result = await self.client.a_get_groups({"search": group_name})
            if not result:
                return OperationResult(
                    success=False,
                    message=f"Grupo '{group_name}' no encontrado",
                    data=None
                )
            if len(result) > 1:
                return OperationResult(
                    success=False,
                    message=f"Se encontraron múltiples grupos con el nombre '{group_name}'",
                    data=None
                )
            group_id = result[0]['id']
            await self.client.a_group_user_add(user_id, group_id)
            return OperationResult(
                success=True,
                message=f'Usuario "{username}" agregado al grupo "{group_name}" exitosamente'
            )
        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.add_to_group", f"usuario '{username}' y grupo '{group_name}'")
    
    async def remove_from_group(self, username: str, group_name: str) -> OperationResult[None]:
        """Remueve un usuario de un grupo"""
        try:
            user_id = await self.client.a_get_user_id(username)
            result = await self.client.a_get_groups({"search": group_name})
            if not result:
                return OperationResult(
                    success=False,
                    message=f"Grupo '{group_name}' no encontrado",
                    data=None
                )
            if len(result) > 1:
                return OperationResult(
                    success=False,
                    message=f"Se encontraron múltiples grupos con el nombre '{group_name}'",
                    data=None
                )
            group_id = result[0]['id']
            await self.client.a_group_user_remove(user_id, group_id)
            return OperationResult(
                success=True,
                message=f'Usuario "{username}" eliminado del grupo "{group_name}" exitosamente'
            )
        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.remove_from_group", f"usuario '{username}' y grupo '{group_name}'")

    async def switch_groups(self, username: str, from_group: str, to_group: str) -> OperationResult[None]:
        """Mueve un usuario de un grupo a otro"""
        try:
            await self.remove_from_group(username, from_group)
            await self.add_to_group(username, to_group)

            return OperationResult(
                success=True,
                message=f'Usuario "{username}" movido del grupo "{from_group}" al grupo "{to_group}" exitosamente'
            )
        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.switch_groups", f"usuario '{username}', desde grupo '{from_group}' a grupo '{to_group}'")


    async def add_attribute(self, username: str, key: str, values: List[str] | str):
        try:
            op = await self.get(username)

            if not op.success:
                return op.error
            
            user = op.data

            if isinstance(values, str):
                values = [values]

            user.attributes.setdefault(key, []).extend(values)

            await self.client.a_update_user(
                user.id,
                user.model_dump()
            )

            return OperationResult(
                success=True,
                message=f'Para el atributo "{key}", agregados los valores {values}, para el usuario "{username}" exitosamente'
            )

        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.add_attribute", f"usuario '{username}', clave '{key}' value '{values}'")

    async def remove_attribute(self, username: str, key: str, values: List[str] | str):
        try:
            op = await self.get(username)

            if not op.success:
                return op.error
            
            user = op.data

            if isinstance(values, str):
                values = [values]

            for value in values:
                if key in user.attributes and value in user.attributes[key]:
                    user.attributes[key].remove(value)

            await self.client.a_update_user(
                user.id,
                user.model_dump()
            )

            return OperationResult(
                success=True,
                message=f'Para el atributo "{key}", eliminados los valores {values}, para el usuario "{username}" exitosamente'
            )

        except Exception as e:
            return KeycloakSDKException(e).handle(f"{self.NAME}.remove_attribute", f"usuario '{username}', clave '{key}' value '{values}'")